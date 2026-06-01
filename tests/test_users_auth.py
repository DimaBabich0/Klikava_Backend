from datetime import timedelta

from app.services.auth import create_token

from conftest import auth_headers, get_user


def assert_status(response, code: int):
  assert response.status_code == code


def assert_rest_status(response, code: int, is_ok: bool):
  body = response.json()
  assert response.status_code == code
  assert body["status"]["code"] == code
  assert body["status"]["is_ok"] is is_ok
  return body


def test_register_creates_active_buyer_user(client):
  response = client.post(
    "/users/register",
    json={
      "login": "newbuyer",
      "email": "newbuyer@example.com",
      "password": "password123",
      "name": "New Buyer",
    },
  )

  body = assert_rest_status(response, 201, True)
  assert body["meta"]["action"] == "register_user"
  assert body["data"]["email"] == "newbuyer@example.com"
  assert body["data"]["is_active"] is True
  assert [role["name"] for role in body["data"]["roles"]] == ["BUYER"]


def test_register_rejects_duplicate_email_and_login(client):
  duplicate_email = client.post(
    "/users/register",
    json={
      "login": "fresh_login",
      "email": "buyer@example.com",
      "password": "password123",
      "name": "Duplicate Email",
    },
  )
  duplicate_login = client.post(
    "/users/register",
    json={
      "login": "buyer",
      "email": "fresh@example.com",
      "password": "password123",
      "name": "Duplicate Login",
    },
  )

  assert_rest_status(duplicate_email, 400, False)
  assert duplicate_email.json()["meta"]["message"] == "Email already exists"
  assert_rest_status(duplicate_login, 400, False)
  assert duplicate_login.json()["meta"]["message"] == "Login already exists"


def test_login_success_returns_bearer_token_and_user(client):
  response = client.post(
    "/users/login",
    json={"login": "admin", "password": "password123"},
  )

  body = assert_rest_status(response, 200, True)
  assert body["data"]["token_type"] == "bearer"
  assert body["data"]["access_token"]
  assert body["data"]["user"]["email"] == "admin@example.com"
  assert [role["name"] for role in body["data"]["user"]["roles"]] == ["ADMIN"]


def test_login_rejects_bad_password_and_inactive_accounts(client):
  wrong_password = client.post(
    "/users/login",
    json={"login": "buyer", "password": "wrong-password"},
  )
  banned = client.post(
    "/users/login",
    json={"login": "banned", "password": "password123"},
  )
  deleted = client.post(
    "/users/login",
    json={"login": "deleted", "password": "password123"},
  )

  assert_rest_status(wrong_password, 401, False)
  assert_rest_status(banned, 401, False)
  assert_rest_status(deleted, 401, False)


def test_protected_route_requires_authorization_header(client):
  response = client.get("/users/me")

  body = assert_rest_status(response, 401, False)
  assert body["meta"]["message"] == "Token not found in request headers"


def test_protected_route_rejects_invalid_token_format(client):
  response = client.get("/users/me", headers={"Authorization": "not-a-bearer-token"})

  body = assert_rest_status(response, 401, False)
  assert body["meta"]["message"] == "Invalid token"


def test_protected_route_rejects_invalid_bearer_token(client):
  response = client.get("/users/me", headers={"Authorization": "Bearer broken.jwt"})

  body = assert_rest_status(response, 401, False)
  assert body["meta"]["message"] == "Invalid token"


def test_protected_route_rejects_expired_token(client, db_session):
  buyer = get_user(db_session, "buyer")
  token = create_token(
    {"sub": str(buyer.id), "roles": ["BUYER"]},
    expires_delta=timedelta(seconds=-1),
  )

  response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

  assert_rest_status(response, 401, False)


def test_protected_route_rejects_invalid_token_payload(client):
  token = create_token({"sub": "not-an-int", "roles": ["BUYER"]})

  response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

  assert_status(response, 401)
  assert response.json()["detail"] == "Invalid token payload"


def test_protected_route_rejects_missing_deleted_and_inactive_users(client, db_session):
  missing_token = create_token({"sub": "9999", "roles": ["BUYER"]})
  banned = get_user(db_session, "banned")
  deleted = get_user(db_session, "deleted")

  missing = client.get("/users/me", headers={"Authorization": f"Bearer {missing_token}"})
  inactive = client.get("/users/me", headers=auth_headers(banned))
  deleted_response = client.get("/users/me", headers=auth_headers(deleted))

  assert_status(missing, 401)
  assert_status(inactive, 401)
  assert_status(deleted_response, 401)


def test_me_returns_current_user(client, db_session):
  buyer = get_user(db_session, "buyer")

  response = client.get("/users/me", headers=auth_headers(buyer))

  body = assert_rest_status(response, 200, True)
  assert body["data"]["id"] == buyer.id
  assert body["data"]["email"] == "buyer@example.com"


def test_list_users_is_limited_to_admin_and_moderator(client, db_session):
  buyer = get_user(db_session, "buyer")
  admin = get_user(db_session, "admin")
  moderator = get_user(db_session, "moderator")

  buyer_response = client.get("/users", headers=auth_headers(buyer))
  admin_response = client.get("/users", headers=auth_headers(admin))
  moderator_response = client.get("/users", headers=auth_headers(moderator))

  assert_rest_status(buyer_response, 403, False)
  admin_body = assert_rest_status(admin_response, 200, True)
  moderator_body = assert_rest_status(moderator_response, 200, True)
  assert len(admin_body["data"]["items"]) >= 7
  assert moderator_body["meta"]["pagination"]["total_items"] >= 7


def test_email_search_is_limited_to_admin_and_moderator(client, db_session):
  buyer = get_user(db_session, "buyer")
  admin = get_user(db_session, "admin")
  moderator = get_user(db_session, "moderator")

  forbidden = client.get("/users/email/buyer@example.com", headers=auth_headers(buyer))
  found_by_admin = client.get("/users/email/buyer@example.com", headers=auth_headers(admin))
  found_by_moderator = client.get("/users/email/buyer@example.com", headers=auth_headers(moderator))
  missing = client.get("/users/email/missing@example.com", headers=auth_headers(admin))

  assert_rest_status(forbidden, 403, False)
  assert_rest_status(found_by_admin, 200, True)
  assert_rest_status(found_by_moderator, 200, True)
  assert_rest_status(missing, 404, False)


def test_get_user_allows_owner_admin_and_moderator(client, db_session):
  buyer = get_user(db_session, "buyer")
  other = get_user(db_session, "other")
  admin = get_user(db_session, "admin")
  moderator = get_user(db_session, "moderator")

  owner_response = client.get(f"/users/{buyer.id}", headers=auth_headers(buyer))
  forbidden = client.get(f"/users/{other.id}", headers=auth_headers(buyer))
  admin_response = client.get(f"/users/{other.id}", headers=auth_headers(admin))
  moderator_response = client.get(f"/users/{other.id}", headers=auth_headers(moderator))
  missing = client.get("/users/9999", headers=auth_headers(admin))

  assert_rest_status(owner_response, 200, True)
  assert_rest_status(forbidden, 403, False)
  assert_rest_status(admin_response, 200, True)
  assert_rest_status(moderator_response, 200, True)
  assert_rest_status(missing, 404, False)


def test_get_user_roles_allows_owner_admin_and_moderator(client, db_session):
  buyer = get_user(db_session, "buyer")
  other = get_user(db_session, "other")
  admin = get_user(db_session, "admin")
  moderator = get_user(db_session, "moderator")

  owner_response = client.get(f"/users/{buyer.id}/roles", headers=auth_headers(buyer))
  forbidden = client.get(f"/users/{other.id}/roles", headers=auth_headers(buyer))
  admin_response = client.get(f"/users/{other.id}/roles", headers=auth_headers(admin))
  moderator_response = client.get(f"/users/{other.id}/roles", headers=auth_headers(moderator))

  owner_body = assert_rest_status(owner_response, 200, True)
  assert [role["name"] for role in owner_body["data"]] == ["BUYER"]
  assert_rest_status(forbidden, 403, False)
  assert_rest_status(admin_response, 200, True)
  assert_rest_status(moderator_response, 200, True)


def test_update_user_allows_owner_and_admin_only(client, db_session):
  buyer = get_user(db_session, "buyer")
  other = get_user(db_session, "other")
  admin = get_user(db_session, "admin")
  moderator = get_user(db_session, "moderator")

  owner_response = client.patch(
    f"/users/{buyer.id}",
    headers=auth_headers(buyer),
    json={"name": "Buyer Updated"},
  )
  admin_response = client.patch(
    f"/users/{other.id}",
    headers=auth_headers(admin),
    json={"name": "Other Updated"},
  )
  moderator_response = client.patch(
    f"/users/{other.id}",
    headers=auth_headers(moderator),
    json={"name": "Moderator Attempt"},
  )

  assert_rest_status(owner_response, 200, True)
  assert owner_response.json()["data"]["name"] == "Buyer Updated"
  assert_rest_status(admin_response, 200, True)
  assert admin_response.json()["data"]["name"] == "Other Updated"
  assert_rest_status(moderator_response, 403, False)


def test_update_user_handles_missing_user_and_duplicate_email(client, db_session):
  buyer = get_user(db_session, "buyer")
  admin = get_user(db_session, "admin")

  duplicate_email = client.patch(
    f"/users/{buyer.id}",
    headers=auth_headers(buyer),
    json={"email": "other@example.com"},
  )
  missing = client.patch(
    "/users/9999",
    headers=auth_headers(admin),
    json={"name": "Missing"},
  )

  assert_rest_status(duplicate_email, 400, False)
  assert duplicate_email.json()["meta"]["message"] == "Email already exists"
  assert_rest_status(missing, 404, False)


def test_ban_user_is_limited_to_admin_and_moderator(client, db_session):
  buyer = get_user(db_session, "buyer")
  other = get_user(db_session, "other")
  admin = get_user(db_session, "admin")
  moderator = get_user(db_session, "moderator")
  seller = get_user(db_session, "seller")

  forbidden = client.post(f"/users/{other.id}/ban", headers=auth_headers(buyer))
  admin_ban = client.post(
    f"/users/{other.id}/ban",
    headers=auth_headers(admin),
    json={"reason": "policy violation"},
  )
  moderator_ban = client.post(f"/users/{seller.id}/ban", headers=auth_headers(moderator))

  assert_rest_status(forbidden, 403, False)
  admin_body = assert_rest_status(admin_ban, 200, True)
  moderator_body = assert_rest_status(moderator_ban, 200, True)
  assert admin_body["meta"]["message"] == "User banned: policy violation"
  assert admin_body["data"]["is_active"] is False
  assert moderator_body["data"]["is_active"] is False


def test_ban_user_rejects_self_ban_and_missing_user(client, db_session):
  admin = get_user(db_session, "admin")

  self_ban = client.post(f"/users/{admin.id}/ban", headers=auth_headers(admin))
  missing = client.post("/users/9999/ban", headers=auth_headers(admin))

  assert_rest_status(self_ban, 400, False)
  assert self_ban.json()["meta"]["message"] == "User cannot ban himself"
  assert_rest_status(missing, 404, False)


def test_require_role_allows_required_role_and_rejects_other_roles(client, db_session):
  buyer = get_user(db_session, "buyer")
  admin = get_user(db_session, "admin")

  allowed = client.get("/admin-only", headers=auth_headers(admin))
  forbidden = client.get("/admin-only", headers=auth_headers(buyer))

  assert allowed.status_code == 200
  assert allowed.json()["user_id"] == admin.id
  assert_status(forbidden, 403)
  assert forbidden.json()["detail"] == "User does not have required role: ADMIN"
