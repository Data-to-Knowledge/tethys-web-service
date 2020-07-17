FROM python:3.8

# RUN apt-get update && apt-get install -y libspatialindex-dev python-rtree

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy hello-cron file to the cron.d directory
# COPY tethys-cron /etc/cron.d/tethys-cron

# Give execution rights on the cron job
# RUN chmod 0644 /etc/cron.d/tethys-cron

# Apply cron job
# RUN crontab /etc/cron.d/tethys-cron

COPY parameters.yml main.py utils.py ./

# CMD ["cron", "-f"]
CMD ["python", "-u", "main.py"]
