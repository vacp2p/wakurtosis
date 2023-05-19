# Use the official Python image as the base image
FROM python:3.11-slim

# Set maintainer label
LABEL Maintainer="Daimakaimura"

# Install curl and Docker CLI
RUN apt-get update && apt-get install -y curl unzip
RUN curl -L -o docker.tgz "https://download.docker.com/linux/static/stable/x86_64/docker-24.0.0.tgz"
RUN tar -xvzf docker.tgz --strip 1 -C /usr/local/bin docker/docker
RUN docker --version

# Clean up unnecessary files
RUN rm docker.tgz
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Create the virtualenv
RUN python -m venv /opt/venv

# Use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory
WORKDIR /cproc-mon

# Copy the requirements file
COPY requirements.txt .

# Perform the installs
RUN pip install -r requirements.txt

# Perform updates to avoid the "chunked" error
RUN pip install --upgrade docker
RUN pip show urllib3
RUN pip install --upgrade urllib3

# Copy the rest of the files over
COPY . .

# Set the PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/cproc-mon/src/"

# Set the entrypoint
ENTRYPOINT ["python", "monitor.py"]
