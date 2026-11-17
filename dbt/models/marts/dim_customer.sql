-- Seuils choisis pour ce générateur : à revoir avec le métier sur de vraies données.
select
    customer_id,
    any_value(country) as country,
    count(*) as order_count,
    round(sum(amount_eur), 2) as revenue_eur,
    case
        when count(*) >= 100 then 'fidele'
        when count(*) >= 10 then 'regulier'
        else 'occasionnel'
    end as segment
from {{ ref('fct_sales') }}
where customer_id is not null
group by customer_id
