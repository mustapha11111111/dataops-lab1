select order_id
from {{ ref('fct_sales') }}
where amount_eur is null
   or amount_eur <= 0
   or quantity <= 0
   or unit_price <= 0
