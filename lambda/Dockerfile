FROM public.ecr.aws/lambda/python:3.9

# 1) Lambda code root
WORKDIR /var/task

# 2) ensure Python looks in /var/task for imports
ENV PYTHONPATH=/var/task:${PYTHONPATH}

# 3) install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) copy your code -- every folder becomes a top‑level package
COPY base       ./base
COPY clean      ./clean
COPY extractors ./extractors
COPY handlers   ./handlers
COPY quality    ./quality
COPY utils      ./utils
COPY logger.py  .

# no CMD here – AWS image_config.command will choose the handler
