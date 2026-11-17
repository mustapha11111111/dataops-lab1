-- Commandes propres sans taux utilisable. Elles ne doivent pas entrer dans les marts.
select
    clean.order_id,
    clean.order_date,
    clean.country,
    clean.currency,
    'taux_absent' as rejection_reason
from {{ ref('int_orders_clean') }} as clean
where clean.currency <> 'EUR'
  and not exists (
      select 1
      from {{ ref('stg_exchange_rates') }} as rates
      where rates.base_currency = 'EUR'
        and rates.quote_currency = clean.currency
        and rates.rate_date <= clean.order_date
        and rates.rate > 0
  )
