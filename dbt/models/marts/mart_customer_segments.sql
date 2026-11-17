select
    segment,
    count(*) as customers,
    round(sum(revenue_eur), 2) as revenue_eur
from {{ ref('dim_customer') }}
group by segment
