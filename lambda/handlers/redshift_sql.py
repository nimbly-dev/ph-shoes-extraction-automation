import os
import json
import logging
from typing import Any, Dict

from redshift.redshift_sql_runner import RedshiftSQLRunner

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context):
    """
    Expects event["body"] JSON:
      { "sql_file_path": "... .sql", "params": { optional dict } }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        path   = body.get("sql_file_path")
        params = body.get("params")

        if not path:
            raise ValueError("Missing 'sql_file_path' in request body")

        runner = RedshiftSQLRunner(sql_file_path=path)
        runner.run(params=params)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "SQL executed", "sql": path}),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        logger.exception("Handler error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
