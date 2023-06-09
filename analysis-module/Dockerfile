# Create the build image
FROM python:3.11-slim AS build-image

# Create the virtualenv
RUN python -m venv /opt/venv

# Use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Perform the installs
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create the production image
FROM python:3.11-slim AS prod-image
LABEL authors="AlbertoSoutullo"

# Copy the requisite files from the build image to the production image
COPY --from=build-image /opt/venv /opt/venv

# Copy the gennet files to the production image
WORKDIR /analysis
COPY . .

# Deploy the virtualenv in production image
ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONPATH "${PYTHONPATH}:src"

# Set the entrypoint
# `docker run -it analysis /bin/sh` vs `docker run -it --entrypoint /bin/sh  analysis` ?
ENTRYPOINT ["python"]