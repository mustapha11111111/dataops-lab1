SELECT *
FROM {{ ref('orders_clean') }}
WHERE quantity <= 0 OR quantity IS NULL
