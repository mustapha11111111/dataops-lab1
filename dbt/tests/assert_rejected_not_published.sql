select rejected.order_id
from {{ ref('int_orders_rejected') }} as rejected
inner join {{ ref('fct_sales') }} as sales
    on rejected.order_id = sales.order_id
where rejected.rejection_reason <> 'doublon_order_id'
