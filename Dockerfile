FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dbt ./dbt
COPY dashboard ./dashboard
COPY contracts ./contracts
COPY tests/fixtures ./tests/fixtures

ENV PYTHONPATH=/app/src
ENV DUCKDB_PATH=/app/data/warehouse.duckdb
ENV DBT_SEND_ANONYMOUS_USAGE_STATS=false

RUN mkdir -p /app/data
EXPOSE 8501

CMD ["python", "-m", "ecommerce_pipeline", "run"]
