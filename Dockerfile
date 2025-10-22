FROM python:3.14-slim-bookworm
#FROM python:3.14

RUN mkdir /app 
COPY smartmeter_datacollector/ /app/smartmeter_datacollector/
COPY pyproject.toml /app 
COPY README.md /app 

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install

CMD ["poetry", "run", "smartmeter-datacollector" ]
