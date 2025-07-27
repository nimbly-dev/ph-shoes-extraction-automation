FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task
ENV PYTHONPATH=/var/task:${PYTHONPATH}

# Install CMake and a C++ compiler so pyarrow can build
RUN yum install -y gcc-c++ make cmake3 \
    && ln -s /usr/bin/cmake3 /usr/bin/cmake

# Upgrade pip & tooling so it can pick up prebuilt wheels
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel

# Now install Python deps (including pyarrow)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
