select
    order_id,
    order_date_raw,
    order_date,
    customer_id,
    country,
    product,
    quantity,
    unit_price,
    currency,
    rejection_reason,
    _source,
    _batch_id,
    _loaded_at
from {{ ref('int_orders_checked') }}
where rejection_reason is not null
