FROM public.ecr.aws/lambda/python:3.9

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy source code
COPY . ${LAMBDA_TASK_ROOT}
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Default handler (can override in Terraform)
CMD ["handlers.extract.lambda_handler"]
