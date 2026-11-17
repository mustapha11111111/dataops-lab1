select
    strftime(order_date, '%Y-%m') as year_month,
    country,
    round(sum(amount_eur), 2) as revenue_eur,
    count(*) as orders_count
from {{ ref('fct_sales') }}
group by 1, 2
