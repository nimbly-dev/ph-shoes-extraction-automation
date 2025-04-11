# Use the official Apache Airflow image with Python 3.10 as the base.
FROM apache/airflow:2.8.1-python3.10

# Switch to root for copying files.
USER root

# Copy requirements.txt to the image.
COPY requirements.txt /requirements.txt

# Switch to airflow user before installing additional packages.
USER airflow

# Install additional Python packages as the airflow user.
RUN pip install --no-cache-dir -r /requirements.txt

# Switch back to root for copying your custom code.
USER root

# Copy your custom DAGs, utils, and lambda_events into the image.
COPY dags/ /opt/airflow/dags/
COPY utils/ /opt/airflow/utils/
COPY lambda_events/ /opt/airflow/lambda_events/

# Switch back to airflow user for runtime security.
USER airflow

# Set the default command to run the Airflow scheduler.
CMD ["airflow", "scheduler"]
