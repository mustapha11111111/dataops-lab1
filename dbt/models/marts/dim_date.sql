select distinct
    order_date as date_day,
    strftime(order_date, '%Y-%m') as year_month,
    dayname(order_date) as day_name,
    dayofweek(order_date) in (0, 6) as is_weekend
from {{ ref('fct_sales') }}
