-- Le test échoue si plus de 20 % des lignes brutes sont rejetées.
select *
from (
    select
        (select count(*) from {{ ref('stg_orders') }}) as n_total,
        (select count(*) from {{ ref('int_orders_rejected') }}) as n_rejected
) as counts
where n_total > 0
  and n_rejected * 1.0 / n_total > 0.20
