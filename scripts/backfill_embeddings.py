#!/usr/bin/env python3
import os
import json
import time
import sys
from datetime import datetime

import snowflake.connector
from openai import OpenAI

# ── CONFIGURATION ───────────────────────────────────────────────────────────────
# How many products to process per batch (up to ~800–1000 short titles per OpenAI call)
BATCH_SIZE = 800

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
    Tries token‐based OAuth first; if no token is provided, falls back to username/password.
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
            schema=schema
        )
    if password:
        return snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema
        )
    raise RuntimeError("No SNOWFLAKE_TOKEN and SNOWFLAKE_PASSWORD is empty. Cannot authenticate.")

# ── BUILD QUERY TO FETCH NEW IDS ───────────────────────────────────────────────────
def build_id_fetch_query():
    """
    Returns a tuple (sql, params) that selects up to BATCH_SIZE distinct IDs (along with
    title, subtitle) from FACT_PRODUCT_SHOES that do not yet exist in EMBEDDING_FACT_PRODUCT_SHOES.
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

    # No date filter: fetch any ID not yet embedded
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
    Executes the SQL from build_id_fetch_query() and returns a list of tuples:
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
    # response.data is a list of objects, each having an .embedding attribute
    return [record.embedding for record in response.data]

# ── UPSERT INTO EMBEDDING_FACT_PRODUCT_SHOES ────────────────────────────────────────
def upsert_embeddings(conn, id_to_vec):
    """
    Given a dict { id: [float,…] }, upsert all embeddings into EMBEDDING_FACT_PRODUCT_SHOES
    in a single MERGE statement. EMBEDDING is stored as a VARIANT via PARSE_JSON().
    """
    embed_table = "PH_SHOES_DB.PRODUCTION_MARTS.EMBEDDING_FACT_PRODUCT_SHOES"

    # Build VALUES rows: ('id','PARSE_JSON(...)', CURRENT_TIMESTAMP())
    rows = []
    for pid, vector in id_to_vec.items():
        v_json = json.dumps(vector).replace("'", "''")
        rows.append(f"('{pid}', PARSE_JSON('{v_json}'), CURRENT_TIMESTAMP())")

    values_clause = ",\n    ".join(rows)

    sql = f"""
    MERGE INTO {embed_table} AS target
    USING (
      VALUES
        {values_clause}
    ) AS src(id, embedding, last_updated)
    ON target.ID = src.id
    WHEN MATCHED THEN UPDATE SET
      target.EMBEDDING = src.embedding,
      target.LAST_UPDATED = src.last_updated
    WHEN NOT MATCHED THEN INSERT (
      ID, EMBEDDING, LAST_UPDATED
    ) VALUES (
      src.id, src.embedding, src.last_updated
    )
    """
    cur = conn.cursor()
    try:
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

        # Combine fields into a single text for embedding (e.g. "title subtitle")
        texts = [f"{titles[i]} {subtitles[i]}".strip() for i in range(num_rows)]

        embeddings = generate_embeddings(openai_client, texts)
        id_to_vec = { ids[i]: embeddings[i] for i in range(num_rows) }

        upsert_embeddings(conn, id_to_vec)

        total_processed += num_rows
        print(f"  → Upserted {num_rows} embeddings. (Total so far: {total_processed})")
        sys.stdout.flush()

        # Optional small throttle to avoid hitting OpenAI rate limits
        time.sleep(0.1)

    conn.close()
    print(f"Embedding upsert complete. Total IDs processed: {total_processed}")
    sys.stdout.flush()

if __name__ == "__main__":
    backfill_loop()
