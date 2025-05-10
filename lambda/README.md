
Test Lambda locally inside the Image Contaienr: python3 -c "import json; from main import lambda_handler; event=json.load(open('event.json')); print(lambda_handler(event, None))"



python3 -c "import json; from main import lambda_handler; event=json.load(open('events/nike_men_all_shoes.json')); print(lambda_handler(event, None))"

python3 -c "import json; from main import lambda_handler; event=json.load(open('events/world_balance_all_shoes.json')); print(lambda_handler(event, None))"


python3 -c "import json; from main import lambda_handler; event=json.load(open('events/hoka_all_shoes.json')); print(lambda_handler(event, None))"

ETL query params
{
  "queryStringParameters": {
    "year":  "2025",
    "month": "05",
    "day":   "04"
  }
}


Run Create fact table:

{
  "sql_file_path": "/app/sql/create_fact_product_shoes.sql"
}