# Use AWS Glue local dev image for Glue 3.0
FROM amazon/aws-glue-libs:glue_libs_3.0.0_image_01

USER root

# Optional: Install extra Python libraries
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy your ETL scripts
WORKDIR /home/glue/scripts
COPY . /home/glue/scripts

ENTRYPOINT ["python3", "clean_asics_data.py"]