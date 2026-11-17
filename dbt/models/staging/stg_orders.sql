-- Staging : typer et normaliser. Aucune ligne n'est supprimée ici.
select
    src.order_id as order_id,
    src.order_date as order_date_raw,
    try_cast(src.order_date as date) as order_date,
    nullif(trim(src.customer_id), '') as customer_id,
    case lower(trim(src.country))
        when 'france' then 'France'
        when 'italy' then 'Italy'
        when 'tunisia' then 'Tunisia'
        when 'morocco' then 'Morocco'
        when 'united states' then 'United States'
        else trim(src.country)
    end as country,
    src.product as product,
    try_cast(src.quantity as integer) as quantity,
    try_cast(src.unit_price as decimal(18, 2)) as unit_price,
    upper(trim(src.currency)) as currency,
    src.data_origin as data_origin,
    src._loaded_at as _loaded_at,
    src._source as _source,
    src._batch_id as _batch_id,
    row_number() over (
        partition by src.order_id
        order by src._loaded_at, src._batch_id, src.product, src.quantity
    ) as _dup_rank
from {{ source('raw', 'orders') }} as src
