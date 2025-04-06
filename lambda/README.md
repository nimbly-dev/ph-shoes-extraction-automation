
Test Lambda locally inside the Image Contaienr: python3 -c "import json; from main import lambda_handler; event=json.load(open('event.json')); print(lambda_handler(event, None))"



python3 -c "import json; from main import lambda_handler; event=json.load(open('events/nike_men_all_shoes.json')); print(lambda_handler(event, None))"

python3 -c "import json; from main import lambda_handler; event=json.load(open('events/world_balance_all_shoes.json')); print(lambda_handler(event, None))"


python3 -c "import json; from main import lambda_handler; event=json.load(open('events/hoka_all_shoes.json')); print(lambda_handler(event, None))"


For running script to push ECR image

1. source .env
2. ./push_lambda_image.sh