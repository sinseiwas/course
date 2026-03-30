def test_login_success_redirects_to_books(client, seeded_users):
    response = client.post(
        "/auth/login",
        data={"email": "admin@test.local", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/books"


def test_login_failure_returns_to_login(client, seeded_users):
    response = client.post(
        "/auth/login",
        data={"email": "admin@test.local", "password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"
