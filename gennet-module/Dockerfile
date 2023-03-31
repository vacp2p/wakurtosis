# Create the build image
FROM python:3.8-slim AS build-image

# Create the virtualenv
RUN python -m venv /opt/venv

# Use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Perform the installs
COPY gennet-module/requirements.txt .
RUN pip install -r requirements.txt

# Create the production image
FROM python:3.8-slim AS prod-image
LABEL authors="0xFugue, Daimakaimura"
#LABEL org.opencontainers.image.authors="0xFugue@github.com, Daimakaimura@github.com"

# Copy the requisite files from the build image to the production image
COPY --from=build-image /opt/venv /opt/venv

# Copy the gennet files to the production image
WORKDIR /config/traits
COPY config/traits .

WORKDIR /config
COPY config/config.json .

WORKDIR /gennet
COPY gennet-module .

# Deploy the virtualenv in production image
ENV PATH="/opt/venv/bin:$PATH"

# Set the entrypoint
ENTRYPOINT ["python", "gennet.py"]

