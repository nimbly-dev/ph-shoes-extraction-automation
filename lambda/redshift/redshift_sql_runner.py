# util/redshift_sql_runner.py

import os
import json
import logging
from typing import Optional, Dict
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
import boto3
import psycopg2

from utils.secrets_util import SecretsUtil

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class RedshiftSQLRunner:
    """
    Load and execute a .sql file against Redshift, with optional Python-format params.
    """

    def __init__(
        self,
        sql_file_path: str,
        secret_name:    Optional[str] = None,
        region:         Optional[str] = None,
    ):
        self.sql_file_path = sql_file_path
        self.secret_name   = secret_name or os.environ["REDSHIFT_SECRET_NAME"]
        self.region        = region or os.environ["AWS_REGION"]

        # prepare secrets‐manager cache
        self._sm_client = boto3.client("secretsmanager", region_name=self.region)
        self._sm_cache  = SecretCache(config=SecretCacheConfig(), client=self._sm_client)

    def _load_sql(self) -> str:
        if not os.path.exists(self.sql_file_path):
            raise FileNotFoundError(f"SQL file not found: {self.sql_file_path}")
        with open(self.sql_file_path, "r") as f:
            return f.read()

    def _get_creds(self) -> dict:
        return SecretsUtil.get_secret(self.secret_name, self.region)

    def run(self, params: Optional[Dict[str,Any]] = None) -> None:
        """
        Execute the SQL script in Redshift.
        If params is provided, does raw_sql.format(**params) before executing.
        """
        raw_sql = self._load_sql()
        sql = raw_sql.format(**params) if params else raw_sql

        creds = self._get_creds()
        conn_str = (
            f"host={creds['host']} port={creds['port']} dbname={creds['dbname']} "
            f"user={creds['username']} password={creds['password']} sslmode=require"
        )

        logger.info(f"Connecting to Redshift {creds['host']}:{creds['port']}/{creds['dbname']}")
        conn = psycopg2.connect(conn_str)
        try:
            with conn:
                with conn.cursor() as cur:
                    logger.info(f"Running SQL (length={len(sql)} chars)")
                    cur.execute(sql)
            logger.info("SQL execution completed successfully.")
        except Exception:
            logger.exception("Error executing Redshift SQL")
            raise
        finally:
            conn.close()
            logger.info("Redshift connection closed.")
