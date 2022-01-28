import pytest

from counter.models import counter_table


@pytest.mark.asyncio
async def test_initial_response(create_test_client):
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 1" in str(body)
