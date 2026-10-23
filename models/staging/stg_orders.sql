{{ config(materialized='view') }}

WITH source_data AS (
    SELECT *
    FROM {{ source('raw', 'orders') }}
)

SELECT
    TRY_CAST(order_id AS INTEGER) AS order_id,
    TRY_CAST(order_date AS DATE) AS order_date,
    NULLIF(TRIM(customer_id), '') AS customer_id,
    CASE
        WHEN LOWER(TRIM(country)) = 'france' THEN 'France'
        WHEN LOWER(TRIM(country)) = 'germany' THEN 'Germany'
        WHEN LOWER(TRIM(country)) = 'italy' THEN 'Italy'
        WHEN LOWER(TRIM(country)) = 'morocco' THEN 'Morocco'
        WHEN LOWER(TRIM(country)) = 'tunisia' THEN 'Tunisia'
        ELSE TRIM(country)
    END AS country,
    TRIM(product) AS product,
    TRY_CAST(quantity AS INTEGER) AS quantity,
    TRY_CAST(unit_price AS DECIMAL(10, 2)) AS unit_price,
    TRY_CAST(_row_number AS BIGINT) AS _row_number,
    _source_file,
    _loaded_at
FROM source_data
