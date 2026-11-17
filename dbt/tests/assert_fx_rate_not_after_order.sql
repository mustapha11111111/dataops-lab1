select order_id
from {{ ref('fct_sales') }}
where fx_rate is null
   or fx_rate <= 0
   or fx_rate_date is null
   or fx_rate_date > order_date
