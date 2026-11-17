from ecommerce_pipeline.flow import daily_sales_flow


def test_prefect_flow_is_importable():
    assert daily_sales_flow.name == "ventes-quotidiennes"
