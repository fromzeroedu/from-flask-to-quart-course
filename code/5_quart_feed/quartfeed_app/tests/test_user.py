import pytest
from quart import current_app
from sqlalchemy import select
from typing import Any

from user.models import user_table


def user_dict() -> dict[str, str]:
    return dict(username="testuser", password="test123")


@pytest.mark.asyncio
async def test_initial_response(create_test_client: Any) -> None:
    response = await create_test_client.get("/login")
    body = await response.get_data()
    assert "Login" in str(body)


@pytest.mark.asyncio
async def test_succesful_registration(
    create_test_client: Any, create_all: Any, create_test_app: Any
) -> None:
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )
    body = await response.get_data()
    assert "You have been registered" in str(body)

    # check that the user was created on the database itself
    async with create_test_app.app_context():
        conn = current_app.dbc  # type: ignore
        query = select([user_table.c.username])
        row = await conn.fetch_one(query=query)
        assert row["username"] == user_dict()["username"]


@pytest.mark.asyncio
async def test_missing_fields_registration(
    create_test_client: Any, create_all: Any
) -> None:
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

    # missing username
    response = await create_test_client.post(
        "/register", form={"username": "", "password": "test123"}
    )
    body = await response.get_data()
    assert "Please enter username and password" in str(body)


@pytest.mark.asyncio
async def test_existing_user_registration(
    create_test_client: Any, create_all: Any
) -> None:
    # create user for the first time
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )

    # create the same user a second time
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )
    body = await response.get_data()
    assert "Username already exists" in str(body)


@pytest.mark.asyncio
async def test_succesful_login(
    create_test_client: Any, create_all: Any, create_test_app: Any
) -> None:
    # creste test user
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )

    response = await create_test_client.post(
        "/login", form=user_dict(), follow_redirects=True
    )
    body = await response.get_data()
    assert "@testuser" in str(body)

    # Check that the session is being set
    async with create_test_client.session_transaction() as sess:
        assert sess["user_id"] == 1


@pytest.mark.asyncio
async def test_user_not_found_login(
    create_test_client: Any, create_all: Any
) -> None:
    # creste test user
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )

    response = await create_test_client.post(
        "/login", form={"username": "testuser2", "password": "test123"}
    )
    body = await response.get_data()
    assert "User not found" in str(body)


@pytest.mark.asyncio
async def test_wrong_password_login(
    create_test_client: Any, create_all: Any
) -> None:
    # creste test user
    response = await create_test_client.post(
        "/register", form=user_dict(), follow_redirects=True
    )

    response = await create_test_client.post(
        "/login", form={"username": "testuser", "password": "wrong123"}
    )
    body = await response.get_data()
    assert "User not found" in str(body)
