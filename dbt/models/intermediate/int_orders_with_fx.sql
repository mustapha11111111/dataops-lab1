-- Conversion vers EUR.
-- Un euro vaut 1. Le taux Frankfurter est le nombre d'unités étrangères pour 1 EUR,
-- donc on divise le montant local par ce taux.
-- Si le jour exact n'existe pas, on prend le dernier taux à cette date ou avant.
with foreign_orders as (
    select
        clean.order_id,
        clean.order_date,
        clean.customer_id,
        clean.country,
        clean.product,
        clean.quantity,
        clean.unit_price,
        clean.currency,
        clean.data_origin,
        rates.rate as fx_rate,
        rates.rate_date as fx_rate_date,
        'taux_anterieur_le_plus_recent' as fx_method
    from {{ ref('int_orders_clean') }} as clean
    inner join {{ ref('stg_exchange_rates') }} as rates
        on rates.base_currency = 'EUR'
        and rates.quote_currency = clean.currency
        and rates.rate_date = (
            select max(earlier.rate_date)
            from {{ ref('stg_exchange_rates') }} as earlier
            where earlier.base_currency = 'EUR'
              and earlier.quote_currency = clean.currency
              and earlier.rate_date <= clean.order_date
              and earlier.rate > 0
        )
    where clean.currency <> 'EUR'
),
euro_orders as (
    select
        clean.order_id,
        clean.order_date,
        clean.customer_id,
        clean.country,
        clean.product,
        clean.quantity,
        clean.unit_price,
        clean.currency,
        clean.data_origin,
        cast(1 as decimal(18, 6)) as fx_rate,
        clean.order_date as fx_rate_date,
        'identite_eur' as fx_method
    from {{ ref('int_orders_clean') }} as clean
    where clean.currency = 'EUR'
),
priced as (
    select * from euro_orders
    union all
    select * from foreign_orders
)
select
    order_id,
    order_date,
    customer_id,
    country,
    product,
    quantity,
    unit_price,
    currency,
    data_origin,
    fx_rate,
    fx_rate_date,
    fx_method,
    cast(cast(quantity as decimal(18, 2)) * unit_price as decimal(18, 2)) as amount_local,
    cast(
        round((cast(quantity as decimal(18, 2)) * unit_price) / fx_rate, 2) as decimal(18, 2)
    ) as amount_eur
from priced
