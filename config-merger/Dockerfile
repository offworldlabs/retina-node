FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir pyyaml mergedeep

# Copy merge script
COPY script/merge_config.py /usr/local/bin/merge_config.py
RUN chmod +x /usr/local/bin/merge_config.py

# Copy default and forced configs (baked in)
COPY ../config/defaults /config/defaults
COPY ../config/forced /config/forced

# The script will be run via docker-compose command
WORKDIR /config

# Default command (can be overridden in docker-compose)
CMD ["python3", "/usr/local/bin/merge_config.py", "/config/defaults", "/data/blah2/config/user.yml", "/config/merged/config.yml", "/data/blah2/config/config.debug.yml"]
