#!/usr/bin/env python3
import os
import json
import time
import sys
import uuid
from datetime import datetime

import snowflake.connector
from openai import OpenAI

# ── CONFIGURATION ───────────────────────────────────────────────────────────────
# You can bump this back up to 500–800 once the “temp‐table” approach is in place.
BATCH_SIZE = 200

def get_env_or_none(key: str):
    val = os.getenv(key)
    return val.strip() if val and val.strip() != "" else None

YEAR  = get_env_or_none("YEAR")
MONTH = get_env_or_none("MONTH")
DAY   = get_env_or_none("DAY")

# ── SNOWFLAKE CONNECTION SETUP ────────────────────────────────────────────────────
def get_snowflake_connection():
    """
    Return a Snowflake connection using environment variables.
    Tries token‐based OAuth first; if none, falls back to username/password.
    """
    account   = os.getenv("SNOWFLAKE_ACCOUNT")
    user      = os.getenv("SNOWFLAKE_USER")
    role      = os.getenv("SNOWFLAKE_ROLE")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database  = os.getenv("SNOWFLAKE_DATABASE")
    schema    = os.getenv("SNOWFLAKE_SCHEMA")
    token     = os.getenv("SNOWFLAKE_TOKEN")
    password  = os.getenv("SNOWFLAKE_PASSWORD")

    if token:
        return snowflake.connector.connect(
            account=account,
            user=user,
            token=token,
            authenticator="oauth",
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema,
            client_session_keep_alive=True
        )
    if password:
        return snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema,
            client_session_keep_alive=True
        )
    raise RuntimeError("No SNOWFLAKE_TOKEN and SNOWFLAKE_PASSWORD provided; cannot authenticate.")

# ── BUILD QUERY TO FETCH NEW IDS ───────────────────────────────────────────────────
def build_id_fetch_query():
    """
    Returns (sql, params) selecting up to BATCH_SIZE distinct IDs (with title & subtitle)
    from FACT_PRODUCT_SHOES that do not yet exist in EMBEDDING_FACT_PRODUCT_SHOES.
    If YEAR/MONTH/DAY are set, restrict to that dwid; otherwise, fetch all missing IDs.
    """
    fact_table  = "PH_SHOES_DB.PRODUCTION_MARTS.FACT_PRODUCT_SHOES"
    embed_table = "PH_SHOES_DB.PRODUCTION_MARTS.EMBEDDING_FACT_PRODUCT_SHOES"

    if YEAR and MONTH and DAY:
        target_dwid = f"{int(YEAR):04d}{int(MONTH):02d}{int(DAY):02d}"
        sql = f"""
        SELECT DISTINCT f.ID, f.TITLE, f.SUBTITLE
        FROM {fact_table} AS f
        LEFT JOIN {embed_table} AS e
          ON f.ID = e.ID
        WHERE f.DWID = %s
          AND e.ID IS NULL
        ORDER BY f.ID
        LIMIT %s
        """
        params = (target_dwid, BATCH_SIZE)
        return sql, params

    sql = f"""
    SELECT DISTINCT f.ID, f.TITLE, f.SUBTITLE
    FROM {fact_table} AS f
    LEFT JOIN {embed_table} AS e
      ON f.ID = e.ID
    WHERE e.ID IS NULL
    ORDER BY f.ID
    LIMIT %s
    """
    params = (BATCH_SIZE,)
    return sql, params

def fetch_id_batch(conn):
    """
    Execute the SQL from build_id_fetch_query() and return a list of tuples:
      [(id, title, subtitle), ...]
    """
    sql, params = build_id_fetch_query()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()

# ── EMBEDDING GENERATION ────────────────────────────────────────────────────────────
def generate_embeddings(openai_client, texts):
    """
    Call OpenAI’s batch-embedding endpoint with a list of strings.
    Returns a list of embedding vectors (each a list of floats).
    """
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return [record.embedding for record in response.data]

# ── CREATE & POPULATE TEMP TABLE ────────────────────────────────────────────────────
def create_temp_table(conn, temp_table_name):
    """
    Create a temporary table with the same structure as EMBEDDING_FACT_PRODUCT_SHOES
    but only for the current session. Columns: ID (VARCHAR), EMBEDDING (VARIANT),
    LAST_UPDATED (TIMESTAMP_LTZ).
    """
    cur = conn.cursor()
    try:
        # Drop if somehow it exists in session
        cur.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
        # Create a temporary (session-scoped) table
        cur.execute(f"""
            CREATE TEMPORARY TABLE {temp_table_name} (
                ID           VARCHAR(16777216),
                EMBEDDING    VARIANT,
                LAST_UPDATED TIMESTAMP_LTZ
            )
        """)
    finally:
        cur.close()

def insert_into_temp_table(conn, temp_table_name, id_to_vec):
    """
    Given a dict { id: [float,...] }, insert each (id, VARIANT embedding, LAST_UPDATED)
    into a Snowflake temporary table using parameter binding. This avoids any
    giant inline JSON literal.
    """
    cur = conn.cursor()
    try:
        sql = (f"INSERT INTO {temp_table_name} (ID, EMBEDDING, LAST_UPDATED) "
               f"VALUES (%s, PARSE_JSON(%s), CURRENT_TIMESTAMP())")
        # Build a list of tuples: [(id, json_string), ...]
        data = [(pid, json.dumps(vec)) for pid, vec in id_to_vec.items()]
        cur.executemany(sql, data)
        conn.commit()
    finally:
        cur.close()

# ── MERGE FROM TEMP TABLE INTO PRIMARY EMBEDDING TABLE ─────────────────────────────
def merge_from_temp(conn, temp_table_name):
    """
    Perform a MERGE from the session’s temp table into EMBEDDING_FACT_PRODUCT_SHOES.
    """
    embed_table = "PH_SHOES_DB.PRODUCTION_MARTS.EMBEDDING_FACT_PRODUCT_SHOES"
    cur = conn.cursor()
    try:
        sql = f"""
        MERGE INTO {embed_table} AS target
        USING {temp_table_name} AS src
        ON target.ID = src.ID
        WHEN MATCHED THEN 
          UPDATE SET 
            target.EMBEDDING = src.EMBEDDING,
            target.LAST_UPDATED = src.LAST_UPDATED
        WHEN NOT MATCHED THEN 
          INSERT (ID, EMBEDDING, LAST_UPDATED)
          VALUES (src.ID, src.EMBEDDING, src.LAST_UPDATED)
        """
        cur.execute(sql)
        conn.commit()
    finally:
        cur.close()

# ── MAIN BACKFILL LOOP ─────────────────────────────────────────────────────────────
def backfill_loop():
    print(f"Starting embedding upsert. YEAR={YEAR}, MONTH={MONTH}, DAY={DAY}")
    sys.stdout.flush()

    conn = get_snowflake_connection()
    openai_client = OpenAI()

    total_processed = 0
    loop_count = 0

    while True:
        loop_count += 1
        batch = fetch_id_batch(conn)
        num_rows = len(batch)
        print(f"[Loop {loop_count}] fetched {num_rows} IDs to embed")
        sys.stdout.flush()

        if not batch:
            print("No more IDs to embed. Exiting.")
            sys.stdout.flush()
            break

        # Separate out IDs, titles, subtitles
        ids       = [row[0] for row in batch]
        titles    = [row[1] for row in batch]
        subtitles = [row[2] or "" for row in batch]

        # Combine fields into a single text for embedding
        texts = [f"{titles[i]} {subtitles[i]}".strip() for i in range(num_rows)]
        embeddings = generate_embeddings(openai_client, texts)
        id_to_vec = { ids[i]: embeddings[i] for i in range(num_rows) }

        # 1) Create a one-time session temp table
        temp_table_name = f"TEMP_EMBED_{uuid.uuid4().hex.upper()}"
        create_temp_table(conn, temp_table_name)

        # 2) Bulk‐insert rows into the temp table with parameter binding
        insert_into_temp_table(conn, temp_table_name, id_to_vec)

        # 3) Merge from temp into EMBEDDING_FACT_PRODUCT_SHOES
        merge_from_temp(conn, temp_table_name)

        total_processed += num_rows
        print(f"  → Upserted {num_rows} embeddings. (Total so far: {total_processed})")
        sys.stdout.flush()

        # Small throttle to avoid OpenAI rate limits
        time.sleep(0.1)

    conn.close()
    print(f"Embedding upsert complete. Total IDs processed: {total_processed}")
    sys.stdout.flush()

if __name__ == "__main__":
    backfill_loop()
