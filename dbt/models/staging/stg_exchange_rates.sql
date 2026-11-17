-- Un seul taux par date, devise de base et devise cotée. Le plus récent chargé gagne.
select
    rate_date,
    base_currency,
    quote_currency,
    rate,
    _loaded_at,
    _source
from (
    select
        try_cast(src.rate_date as date) as rate_date,
        upper(trim(src.base_currency)) as base_currency,
        upper(trim(src.quote_currency)) as quote_currency,
        try_cast(src.rate as decimal(18, 6)) as rate,
        src._loaded_at,
        src._source,
        row_number() over (
            partition by
                try_cast(src.rate_date as date),
                upper(trim(src.base_currency)),
                upper(trim(src.quote_currency))
            order by src._loaded_at desc
        ) as _rn
    from {{ source('raw', 'exchange_rates') }} as src
) as ranked
where _rn = 1
  and rate_date is not null
  and rate is not null
  and rate > 0
