FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task
ENV PYTHONPATH=/var/task:${PYTHONPATH}

# install Python deps
COPY requirements.txt .
RUN pip install --no‑cache‑dir -r requirements.txt

# copy EVERYTHING (code, handlers, clean/, quality/, etc.)
COPY . .
