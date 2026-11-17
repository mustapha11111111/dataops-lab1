select
    order_id,
    order_date,
    customer_id,
    country,
    product,
    currency,
    quantity,
    unit_price,
    amount_local,
    fx_rate,
    fx_rate_date,
    fx_method,
    amount_eur,
    data_origin
from {{ ref('int_orders_with_fx') }}
