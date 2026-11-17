select
    product,
    count(*) as order_count,
    round(sum(amount_eur), 2) as revenue_eur
from {{ ref('fct_sales') }}
group by product
