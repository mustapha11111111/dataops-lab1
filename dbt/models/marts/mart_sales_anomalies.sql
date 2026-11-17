-- Une journée est anormale si elle s'écarte fortement de la médiane du pays.
-- Il faut au moins 7 jours. Le pic du générateur est volontaire et sert à la démo.
with daily as (
    select
        order_date,
        country,
        sum(amount_eur) as revenue_eur,
        count(*) as orders_count
    from {{ ref('fct_sales') }}
    group by order_date, country
),
stats as (
    select
        country,
        count(*) as observed_days,
        median(revenue_eur) as median_revenue_eur
    from daily
    group by country
)
select
    daily.order_date,
    daily.country,
    round(daily.revenue_eur, 2) as revenue_eur,
    daily.orders_count,
    stats.observed_days,
    round(stats.median_revenue_eur, 2) as median_revenue_eur,
    case
        when stats.observed_days < 7 then 'historique_insuffisant'
        when daily.revenue_eur > 2.5 * stats.median_revenue_eur then 'hausse_anormale'
        when daily.revenue_eur < 0.4 * stats.median_revenue_eur then 'baisse_anormale'
        else 'normal'
    end as anomaly_type
from daily
inner join stats on daily.country = stats.country
