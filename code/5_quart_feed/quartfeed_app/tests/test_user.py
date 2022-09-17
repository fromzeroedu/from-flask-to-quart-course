import pytest
from quart import current_app

from user.models import user_table

def user_dict():
    return dict(username="esfoobar", password="test123")

@pytest.mark.asyncio
async def test_initial_response(create_test_client):
    response = await create_test_client.get("/login")
    body = await response.get_data()
    assert "Login" in str(body)


@pytest.mark.asyncio
async def test_succesful_registration(create_test_client, create_all, create_test_app):
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )

    pass