-- Compare les 30 derniers jours à la fenêtre des 30 jours d'avant.
with bounds as (
    select max(order_date) as max_date
    from {{ ref('fct_sales') }}
),
lines as (
    select
        sales.product,
        sum(
            case
                when sales.order_date > bounds.max_date - interval 30 day then sales.amount_eur
                else 0
            end
        ) as revenue_recent_eur,
        sum(
            case
                when sales.order_date <= bounds.max_date - interval 30 day
                    and sales.order_date > bounds.max_date - interval 60 day
                    then sales.amount_eur
                else 0
            end
        ) as revenue_previous_eur
    from {{ ref('fct_sales') }} as sales
    cross join bounds
    group by sales.product
)
select
    product,
    revenue_recent_eur,
    revenue_previous_eur,
    revenue_recent_eur - revenue_previous_eur as revenue_delta_eur,
    case
        when revenue_previous_eur = 0 then null
        else round((revenue_recent_eur - revenue_previous_eur) / revenue_previous_eur, 4)
    end as variation_pct
from lines
