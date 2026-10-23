SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE reject_reason IS NOT NULL) AS rejected_rows
FROM {{ ref('int_orders_checked') }}
HAVING
    COUNT(*) FILTER (WHERE reject_reason IS NOT NULL) * 1.0
    / NULLIF(COUNT(*), 0) > 0.20
