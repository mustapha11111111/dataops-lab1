select
    order_id,
    order_date,
    customer_id,
    country,
    product,
    quantity,
    unit_price,
    currency,
    data_origin
from {{ ref('int_orders_checked') }}
where rejection_reason is null
