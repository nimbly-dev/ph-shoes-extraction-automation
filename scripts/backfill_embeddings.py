#!/usr/bin/env python3
import os
import json
import time
from datetime import datetime

import snowflake.connector
from openai import OpenAI

# ── CONFIGURATION ───────────────────────────────────────────────────────────────

# How many rows to process per batch.
BATCH_SIZE = 500

# These environment variables, if set, override "process all nulls" behavior:
#   YEAR  → e.g. "2025"
#   MONTH → e.g. "06"
#   DAY   → e.g. "01"
#
# If none of YEAR/MONTH/DAY are set, the script will fetch ANY row with embedding IS NULL
# (to catch whichever days still need backfill). If all three are set, it will only target
# that single dwid (YYYYMMDD).
#
# Example usages:
#   - Nightly:                     (no YEAR/MONTH/DAY set) → process all nulls.
#   - Manual for June 1, 2025:     YEAR=2025, MONTH=06, DAY=01
#   - Manual for today (implicit): (no args) → uses nulls
#


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
    Supports in order:
      1) Programmatic Access Token (SNOWFLAKE_TOKEN with authenticator='oauth')
      2) Private-key auth (SNOWFLAKE_PRIVATE_KEY_PATH + passphrase)
      3) Fallback to username/password (SNOWFLAKE_PASSWORD)
    """
    account   = os.getenv("SNOWFLAKE_ACCOUNT")
    user      = os.getenv("SNOWFLAKE_USER")
    role      = os.getenv("SNOWFLAKE_ROLE")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database  = os.getenv("SNOWFLAKE_DATABASE")
    schema    = os.getenv("SNOWFLAKE_SCHEMA")

    # 1) If SNOWFLAKE_TOKEN is set, use token-based OAuth
    token = os.getenv("SNOWFLAKE_TOKEN")
    print(f"DEBUG ➤ SNOWFLAKE_TOKEN is {'set' if token else 'NOT set'}.")  # remains for debugging
    if token:
        return snowflake.connector.connect(
            account=account,
            user=user,
            token=token,
            authenticator="oauth",         # <--- tell the connector to use OAuth
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema
        )

    # 2) If a private-key path is provided, use key-pair authentication
    private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path:
        with open(private_key_path, "rb") as keyfile:
            p8 = keyfile.read()
        return snowflake.connector.connect(
            account=account,
            user=user,
            private_key=p8,
            private_key_password=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema
        )

    # 3) Otherwise, fall back to username/password
    print("ERROR ➤ No token or private key found; falling back to SNOWFLAKE_PASSWORD.")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    if not password:
        raise RuntimeError(
            "No SNOWFLAKE_TOKEN (OAuth), no SNOWFLAKE_PRIVATE_KEY_PATH (key‐pair), "
            "and SNOWFLAKE_PASSWORD is empty. Cannot authenticate."
        )
    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database=database,
        schema=schema
    )



# ── FETCH & BACKFILL LOGIC ─────────────────────────────────────────────────────────

def build_fetch_query():
    """
    Build the SELECT query for fetching rows needing embeddings.
    - If YEAR, MONTH, DAY are all set, target that single dwid = 'YYYYMMDD'.
    - Otherwise, fetch any row where embedding IS NULL (across all dates),
      ordering by dwid asc, id asc so we fill oldest first.
    """
    if YEAR and MONTH and DAY:
        # Ensure zero‐pad month/day
        target_dwid = f"{int(YEAR):04d}{int(MONTH):02d}{int(DAY):02d}"
        return (
            "SELECT id, title, subtitle "
            "FROM FACT_PRODUCT_SHOES "
            "WHERE dwid = %s "
            "  AND embedding IS NULL "
            "ORDER BY id "
            "LIMIT %s",
            (target_dwid, BATCH_SIZE)
        )
    else:
        # No explicit date → fetch any nulls
        return (
            "SELECT id, title, subtitle "
            "FROM FACT_PRODUCT_SHOES "
            "WHERE embedding IS NULL "
            "ORDER BY dwid, id "
            "LIMIT %s",
            (BATCH_SIZE,)
        )


def fetch_batch(conn):
    """
    Fetch one batch of rows needing embedding:
    - Returns a list of tuples: [(id, title, subtitle), ...].
    """
    sql, params = build_fetch_query()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def generate_embeddings(openai_client, texts):
    """
    Call OpenAI’s Embedding API on a list of text strings.
    Returns a list of embedding vectors (each is a list of floats).
    """
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return [record["embedding"] for record in response["data"]]


def update_batch(conn, id_to_vec):
    """
    Given a dict { id: [float,…] }, update each row’s embedding column in Snowflake.
    """
    cur = conn.cursor()
    try:
        sql = "UPDATE FACT_PRODUCT_SHOES SET embedding = PARSE_JSON(%s) WHERE id = %s"
        for row_id, vector in id_to_vec.items():
            cur.execute(sql, (json.dumps(vector), row_id))
        conn.commit()
    finally:
        cur.close()


def backfill_loop():
    """
    Main loop: repeatedly fetch a batch of rows needing embeddings,
    generate their embeddings via OpenAI, and update Snowflake.
    Stops when no more rows match the criteria.
    """
    print(f" Starting backfill. YEAR={YEAR}, MONTH={MONTH}, DAY={DAY}")
    conn = get_snowflake_connection()
    openai_client = OpenAI()  # reads OPENAI_API_KEY from env

    total_count = 0
    while True:
        batch_rows = fetch_batch(conn)
        if not batch_rows:
            print(" No more rows to embed. Exiting.")
            break

        texts = [f"{row[1]} {row[2] or ''}".strip() for row in batch_rows]
        embeddings = generate_embeddings(openai_client, texts)

        # Build id→embedding mapping
        mapping = {batch_rows[i][0]: embeddings[i] for i in range(len(batch_rows))}
        update_batch(conn, mapping)

        total_count += len(batch_rows)
        print(f"  Updated {len(batch_rows)} embeddings. (Total so far: {total_count})")

        # Throttle just a bit to avoid hitting rate limits
        time.sleep(1)

    conn.close()
    print(f" Backfill complete. Total embeddings updated: {total_count}")


if __name__ == "__main__":
    backfill_loop()
