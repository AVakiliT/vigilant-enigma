import pytest
import requests

from allocation import config


def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    r = requests.post(
        f'{url}/batch/add',
        json={'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta}
    )
    assert r.status_code == 201

@pytest.mark.usefixtures('restart_api')
@pytest.mark.usefixtures('postgres_db')
def test_happy_path_returns_201_and_allocated_batch():
    post_to_add_batch("later", "sku_123123", 100, '2020-01-02')
    post_to_add_batch("early", "sku_123123", 100, '2020-01-01')
    post_to_add_batch("other", "other", 100, None)
    url = config.get_api_url()
    r = requests.post(
        f'{url}/batch/allocate',
        json={'orderid': 'orderid', 'sku': 'sku_123123', 'qty': 3}
    )
    assert r.status_code == 201
    assert r.json()['batch_ref'] == 'early'


@pytest.mark.skip
def test_unhappy_path_returns_400_and_error_message():
    pass


