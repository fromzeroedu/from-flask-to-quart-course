import pytest
from typing import Any


def user_dict(username: str) -> dict[str, str]:
    return dict(username=username, password="test123")


@pytest.mark.asyncio
async def test_succesful_follow_and_unfollow(
    create_test_client: Any, create_all: Any, create_test_app: Any
) -> None:
    # create users
    await create_test_client.post("/register", form=user_dict("testuser1"))
    await create_test_client.post("/register", form=user_dict("testuser2"))

    # login as testuser1
    await create_test_client.post("/login", form=user_dict("testuser1"))

    # visit testuser2's profile
    response = await create_test_client.get("/user/testuser2")
    body = await response.get_data()
    assert "@testuser2" in str(body)

    # follow testuser2
    await create_test_client.get("/add_friend/testuser2")

    # visit the profile again to get flashed message
    response = await create_test_client.get("/user/testuser2")
    body = await response.get_data()
    assert "Followed testuser2" in str(body)

    # unfollow testuser2
    await create_test_client.get("/remove_friend/testuser2")

    # visit the profile again to get flashed message
    response = await create_test_client.get("/user/testuser2")
    body = await response.get_data()
    assert "Unfollowed testuser2" in str(body)
