FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task
ENV PYTHONPATH=/var/task:${PYTHONPATH}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .
