import pytest
from quart import current_app
from sqlalchemy import select

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
    body = await response.get_data()
    assert "You have been registered" in str(body)

    # check that the user was created on the database itself
    async with create_test_app.app_context():
        conn = current_app.dbc
        query = select([user_table.c.username])
        row = await conn.fetch_one(query=query)
        assert row["username"] == user_dict()["username"]


@pytest.mark.asyncio
async def test_missing_fields_registration(create_test_client, create_all):
    # no fields
    response = await create_test_client.post(
        "/register", form={"username": "", "password": ""}
    )
    body = await response.get_data()
    assert "Please enter username and password" in str(body)

    # missing password
    response = await create_test_client.post(
        "/register", form={"username": "testuser", "password": ""}
    )
    body = await response.get_data()
    assert "Please enter username and password" in str(body)    