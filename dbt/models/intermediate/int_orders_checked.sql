-- Première raison de rejet. NULL signifie que la ligne peut être publiée.
select
    staged.*,
    case
        when staged.order_id is null or trim(staged.order_id) = '' then 'order_id_manquant'
        when staged.order_date is null then 'date_invalide'
        when staged.quantity is null or staged.quantity <= 0 then 'quantite_invalide'
        when staged.unit_price is null or staged.unit_price <= 0 then 'prix_invalide'
        when staged.currency is null
            or staged.currency not in ('EUR', 'USD', 'TND', 'MAD') then 'devise_inconnue'
        when staged._dup_rank > 1 then 'doublon_order_id'
    end as rejection_reason
from {{ ref('stg_orders') }} as staged
