select
    order_date,
    country,
    round(sum(amount_eur), 2) as revenue_eur,
    count(*) as orders_count
from {{ ref('fct_sales') }}
group by order_date, country
