select country
from (
    select country, count(distinct currency) as n_currencies
    from {{ ref('fct_sales') }}
    group by country
) as currencies
where n_currencies > 1
