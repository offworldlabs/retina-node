FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir pyyaml mergedeep

# Copy merge script
COPY config-merger/script/merge_config.py /usr/local/bin/merge_config.py
RUN chmod +x /usr/local/bin/merge_config.py

# Create config directories
RUN mkdir -p /config/defaults

# Copy default and forced configs (baked in)
COPY config/default.yml /config/defaults/default.yml
COPY config/forced.yml /config/defaults/forced.yml

# The script will be run via docker-compose command
WORKDIR /config

# Default command (can be overridden in docker-compose)
# Args: <defaults_dir> <user_config> <output_config>
CMD ["python3", "/usr/local/bin/merge_config.py", "/config/defaults", "/data/retina-node/config/user.yml", "/data/retina-node/config/config.yml"]
