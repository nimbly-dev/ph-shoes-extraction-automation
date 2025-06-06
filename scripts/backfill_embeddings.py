#!/usr/bin/env python3
import os
import json
import time
import sys
import uuid
from datetime import datetime
from math import ceil

import snowflake.connector
from openai import OpenAI
import concurrent.futures

# ── CONFIGURATION ───────────────────────────────────────────────────────────────
# How many products to process per batch; adjust upward if needed.
BATCH_SIZE = 500

# How many threads to use for parallel embedding calls.
NUM_THREADS = 5

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
    Prefers token-based OAuth; falls back to username/password.
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
    raise RuntimeError("No SNOWFLAKE_TOKEN or SNOWFLAKE_PASSWORD provided; cannot authenticate.")

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
    Returns a list of embedding vectors (each a Python list of floats).
    """
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return [record.embedding for record in response.data]

# ── CREATE & POPULATE TEMP TABLE ───────────────────────────────────────────────────
def create_temp_table(conn, temp_table_name):
    """
    Create a session-scoped temporary table with columns:
    ID (VARCHAR), EMBEDDING (VARIANT), LAST_UPDATED (TIMESTAMP_LTZ).
    """
    cur = conn.cursor()
    try:
        cur.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
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
    Given dict { id: [float,…] }, insert each (ID, embedding) pair individually,
    converting the embedding list to JSON and letting PARSE_JSON(...) turn it into VARIANT.
    """
    cur = conn.cursor()
    try:
        sql = f"""
        INSERT INTO {temp_table_name} (ID, EMBEDDING, LAST_UPDATED)
        SELECT %s, PARSE_JSON(%s), CURRENT_TIMESTAMP()
        """
        for pid, vec in id_to_vec.items():
            if not isinstance(vec, list):
                raise RuntimeError(f"Embedding for ID={pid} is not a list: {type(vec)}")
            json_str = json.dumps(vec)
            cur.execute(sql, (pid, json_str))
        conn.commit()
    finally:
        cur.close()

# ── MERGE FROM TEMP TABLE INTO PRIMARY EMBEDDING TABLE ─────────────────────────────
def merge_from_temp(conn, temp_table_name):
    """
    Perform a MERGE from the session’s temporary table into EMBEDDING_FACT_PRODUCT_SHOES.
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

# ── MAIN BACKFILL LOOP WITH THREADING ───────────────────────────────────────────────
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

        # Extract IDs, titles, subtitles
        ids       = [row[0] for row in batch]
        titles    = [row[1] for row in batch]
        subtitles = [row[2] or "" for row in batch]

        # Build texts for embedding
        texts = [f"{titles[i]} {subtitles[i]}".strip() for i in range(num_rows)]

        # Split into roughly NUM_THREADS chunks
        chunk_size = int(ceil(num_rows / NUM_THREADS))
        chunks = [
            texts[i * chunk_size : min((i + 1) * chunk_size, num_rows)]
            for i in range(NUM_THREADS)
        ]
        id_chunks = [
            ids[i * chunk_size : min((i + 1) * chunk_size, num_rows)]
            for i in range(NUM_THREADS)
        ]

        # If the last chunk ends up empty (because num_rows < NUM_THREADS), remove it
        filtered = [
            (id_chunks[i], chunks[i])
            for i in range(len(chunks))
            if chunks[i]
        ]

        # Use ThreadPoolExecutor to generate embeddings in parallel
        id_to_vec: Dict[str, List[float]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = []
            for id_chunk, text_chunk in filtered:
                futures.append(
                    executor.submit(generate_embeddings, openai_client, text_chunk)
                )

            # As each future completes, collect its embeddings and map back to IDs
            for future_idx, future in enumerate(concurrent.futures.as_completed(futures)):
                embedding_list = future.result()
                # Determine which chunk this corresponds to:
                # We can match by index of future in the original `futures` list.
                chunk_index = futures.index(future)
                ids_for_chunk = filtered[chunk_index][0]
                if len(ids_for_chunk) != len(embedding_list):
                    raise RuntimeError(
                        f"Chunk size mismatch: {len(ids_for_chunk)} IDs vs {len(embedding_list)} embeddings"
                    )
                for idx_in_chunk, pid in enumerate(ids_for_chunk):
                    id_to_vec[pid] = embedding_list[idx_in_chunk]

        # 1) Create a session-scoped temporary table
        temp_table_name = f"TEMP_EMBED_{uuid.uuid4().hex.upper()}"
        create_temp_table(conn, temp_table_name)

        # 2) Bulk-insert into temp using Python lists for VARIANT binding
        insert_into_temp_table(conn, temp_table_name, id_to_vec)

        # 3) Merge from temp into EMBEDDING_FACT_PRODUCT_SHOES
        merge_from_temp(conn, temp_table_name)

        total_processed += num_rows
        print(f"  → Upserted {num_rows} embeddings. (Total so far: {total_processed})")
        sys.stdout.flush()

        # Small delay to respect OpenAI rate limits
        time.sleep(0.1)

    conn.close()
    print(f"Embedding upsert complete. Total IDs processed: {total_processed}")
    sys.stdout.flush()

if __name__ == "__main__":
    backfill_loop()
