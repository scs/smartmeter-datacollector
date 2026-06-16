####################
# Builder
####################
FROM python:3.13-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip3 install --no-cache-dir poetry~=2.1

# Copy only meta data first
COPY pyproject.toml poetry.lock ./

# Create virtualenv and install only dependencies
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy the source files
COPY . ./

# Build wheel
RUN poetry build --format=wheel --no-ansi --output="./dist"

####################
# Runtime
####################
FROM python:3.13-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy the built wheel from builder stage
COPY --from=builder /app/dist/*.whl /tmp/

# Install wheel package
RUN pip3 install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Create default config file
RUN mkdir /data && smartmeter-datacollector -s -c /data/datacollector.ini

VOLUME [ "/data" ]

CMD ["smartmeter-datacollector", "-c", "/data/datacollector.ini"]
