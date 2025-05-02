FROM public.ecr.aws/lambda/python:3.9

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="${LAMBDA_TASK_ROOT}:${PYTHONPATH}"

# Copy your code
COPY . ${LAMBDA_TASK_ROOT}