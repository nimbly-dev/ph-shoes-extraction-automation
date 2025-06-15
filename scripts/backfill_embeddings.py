#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
from math import ceil
from datetime import datetime
from typing import List, Dict, Optional

import snowflake.connector
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIGURATION ───────────────────────────────────────────────────────────────
BATCH_SIZE  = 500
NUM_THREADS = 5

def get_env_or_none(key: str) -> Optional[str]:
    val = os.getenv(key)
    return val.strip() if val and val.strip() != "" else None

YEAR  = get_env_or_none("YEAR")
MONTH = get_env_or_none("MONTH")
DAY   = get_env_or_none("DAY")

# ── SNOWFLAKE CONNECTION ─────────────────────────────────────────────────────────
def get_snowflake_connection():
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

# ── BUILD FETCH QUERY ────────────────────────────────────────────────────────────
def build_id_fetch_query():
    fact_table  = "PH_SHOES_DB.PRODUCTION_MARTS.FACT_PRODUCT_SHOES"
    embed_table = "PH_SHOES_DB.PRODUCTION_MARTS.EMBEDDING_FACT_PRODUCT_SHOES"

    # Validate YEAR/MONTH/DAY usage
    if any([YEAR, MONTH, DAY]) and not all([YEAR, MONTH, DAY]):
        raise RuntimeError("YEAR, MONTH, and DAY must all be set or all unset.")

    if YEAR and MONTH and DAY:
        dwid = f"{int(YEAR):04d}{int(MONTH):02d}{int(DAY):02d}"
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
        return sql, (dwid, BATCH_SIZE)

    sql = f"""
        SELECT DISTINCT f.ID, f.TITLE, f.SUBTITLE
        FROM {fact_table} AS f
        LEFT JOIN {embed_table} AS e
          ON f.ID = e.ID
        WHERE e.ID IS NULL
        ORDER BY f.ID
        LIMIT %s
    """
    return sql, (BATCH_SIZE,)

def fetch_id_batch(conn) -> List[tuple]:
    sql, params = build_id_fetch_query()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()

# ── EMBEDDING WITH RETRIES ─────────────────────────────────────────────────────────
def generate_embeddings(openai_client: OpenAI, texts: List[str]) -> List[List[float]]:
    max_retries = 3
    delay = 1
    for attempt in range(1, max_retries + 1):
        try:
            resp = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [r.embedding for r in resp.data]
        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay *= 2

# ── TEMP TABLE MANAGEMENT ──────────────────────────────────────────────────────────
def create_temp_table(conn, temp_table_name: str):
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

def sanitize_vec(vec: List[float], decimals: int = 6) -> List[float]:
    return [round(float(x), decimals) for x in vec]

def insert_into_temp_table(conn, temp_table_name: str, id_to_vec: Dict[str, List[float]]):
    cur = conn.cursor()
    try:
        for pid, vec in id_to_vec.items():
            # 1) round to shave off extra precision (Snowflake chokes on >17‐digit floats)
            clean_vec = sanitize_vec(vec)

            # 2) JSON‐dump without spaces
            json_text = json.dumps(clean_vec, separators=(",", ":"))

            # 3) escape any single quotes in your ID
            pid_escaped = pid.replace("'", "''")

            # 4) inline literal into SQL
            sql = f"""
                INSERT INTO {temp_table_name} (ID, EMBEDDING, LAST_UPDATED)
                SELECT '{pid_escaped}', PARSE_JSON('{json_text}'), CURRENT_TIMESTAMP()
            """
            cur.execute(sql)

        conn.commit()
    finally:
        cur.close()


# ── MERGE WITH CONDITIONAL UPDATE ─────────────────────────────────────────────────
def merge_from_temp(conn, temp_table_name: str):
    embed_table = "PH_SHOES_DB.PRODUCTION_MARTS.EMBEDDING_FACT_PRODUCT_SHOES"
    cur = conn.cursor()
    try:
        sql = f"""
            MERGE INTO {embed_table} AS target
            USING {temp_table_name} AS src
              ON target.ID = src.ID
            WHEN MATCHED AND target.EMBEDDING != src.EMBEDDING THEN
              UPDATE SET 
                target.EMBEDDING    = src.EMBEDDING,
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

    total = 0
    loop = 0

    while True:
        loop += 1
        batch = fetch_id_batch(conn)
        if not batch:
            print("No more IDs to embed. Exiting.")
            break

        print(f"[Loop {loop}] fetched {len(batch)} IDs")
        sys.stdout.flush()

        ids       = [row[0] for row in batch]
        titles    = [row[1] for row in batch]
        subtitles = [row[2] or "" for row in batch]

        texts = [f"{titles[i]} {subtitles[i]}".strip() for i in range(len(batch))]

        # chunk for threading
        chunk_size = ceil(len(batch) / NUM_THREADS)
        chunks = [
            texts[i*chunk_size : min((i+1)*chunk_size, len(batch))]
            for i in range(NUM_THREADS)
        ]
        id_chunks = [
            ids[i*chunk_size : min((i+1)*chunk_size, len(batch))]
            for i in range(NUM_THREADS)
        ]

        filtered = [
            (id_chunks[i], chunks[i])
            for i in range(len(chunks))
            if chunks[i]
        ]

        # parallel embedding with robust mapping
        id_to_vec: Dict[str, List[float]] = {}
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            future_map = {
                executor.submit(generate_embeddings, openai_client, texts): ids
                for ids, texts in filtered
            }
            for future in as_completed(future_map):
                ids_chunk = future_map[future]
                embedding_list = future.result()
                if len(ids_chunk) != len(embedding_list):
                    raise RuntimeError(
                        f"Chunk mismatch: {len(ids_chunk)} IDs vs {len(embedding_list)} embeddings"
                    )
                for pid, vec in zip(ids_chunk, embedding_list):
                    id_to_vec[pid] = vec

        # write & merge
        temp_tbl = f"TEMP_EMBED_{uuid.uuid4().hex.upper()}"
        create_temp_table(conn, temp_tbl)
        insert_into_temp_table(conn, temp_tbl, id_to_vec)
        merge_from_temp(conn, temp_tbl)

        total += len(batch)
        print(f"  → Upserted {len(batch)} embeddings (total {total})")
        sys.stdout.flush()

        time.sleep(0.1)

    conn.close()
    print(f"Completed. Total IDs processed: {total}")
    sys.stdout.flush()

if __name__ == "__main__":
    backfill_loop()
