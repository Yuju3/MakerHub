"""Regression tests for registration, login, and project collaboration."""

import pytest


def read_database(database):
    """Snapshot the users and projects collections as plain lists."""
    return {
        "users": list(database.users.find({}, {"_id": 0})),
        "projects": list(database.projects.find({}, {"_id": 0})),
    }


def test_registration_persists_user_without_exposing_password(client, database):
    user = {"username": "alice", "userId": "u1", "password": "test-password"}
    response = client.post("/add_user", json=user)
    assert response.status_code == 201
    assert response.get_json() == {"username": "alice", "userId": "u1", "projects": []}
    assert read_database(database)["users"] == [{**user, "projects": []}]


@pytest.mark.parametrize("field", ["username", "userId", "password"])
@pytest.mark.parametrize("value", [None, ""])
def test_registration_requires_fields(client, database, field, value):
    data = {"username": "alice", "userId": "u1", "password": "test-password"}
    if value is None:
        del data[field]
    else:
        data[field] = value
    response = client.post("/add_user", json=data)
    assert response.status_code == 400
    assert "required" in response.get_json()["error"]
    assert read_database(database)["users"] == []


@pytest.mark.parametrize("field", ["username", "userId"])
def test_registration_rejects_duplicate_identity(client, owner, database, field):
    before = read_database(database)
    data = {"username": "bob", "userId": "u2", "password": "other-password"}
    data[field] = owner[field]
    response = client.post("/add_user", json=data)
    assert response.status_code == 409
    assert read_database(database) == before


def test_login_returns_public_user(client, owner):
    response = client.post("/login", json=owner)
    assert response.status_code == 200
    assert response.get_json() == {"username": "alice", "userId": "u1", "projects": []}


@pytest.mark.parametrize("credentials", [
    {"username": "alice", "password": "wrong"},
    {"username": "unknown", "password": "test-password"},
    {"username": "alice"},
    {},
])
def test_login_rejects_invalid_credentials(client, owner, database, credentials):
    before = read_database(database)
    response = client.post("/login", json=credentials)
    assert response.status_code == 401
    assert response.get_json() == {"error": "invalid username or password"}
    assert read_database(database) == before


def test_create_project_links_owner_and_persists_description(client, owner, database):
    data = {"projectId": "p1", "name": "Robot", "ownerId": "u1", "description": "Build a robot"}
    response = client.post("/create_project", json=data)
    assert response.status_code == 201
    assert response.get_json() == {**data, "members": ["u1"]}
    snapshot = read_database(database)
    assert snapshot["projects"] == [response.get_json()]
    assert snapshot["users"][0]["projects"] == ["p1"]


@pytest.mark.parametrize("field", ["projectId", "name", "ownerId"])
@pytest.mark.parametrize("value", [None, ""])
def test_create_project_requires_fields(client, owner, database, field, value):
    data = {"projectId": "p1", "name": "Robot", "ownerId": "u1"}
    if value is None:
        del data[field]
    else:
        data[field] = value
    before = read_database(database)
    assert client.post("/create_project", json=data).status_code == 400
    assert read_database(database) == before


def test_create_project_rejects_unknown_owner(client, database):
    response = client.post("/create_project", json={"projectId": "p1", "name": "Robot", "ownerId": "missing"})
    assert response.status_code == 404
    assert read_database(database)["projects"] == []


def test_duplicate_project_does_not_overwrite_original(client, project, database):
    before = read_database(database)
    response = client.post("/create_project", json={**project, "name": "Replacement"})
    assert response.status_code == 409
    assert read_database(database) == before


def test_join_project_updates_both_sides_without_duplicates(client, project, database):
    assert client.post("/add_user", json={"username": "bob", "userId": "u2", "password": "secret"}).status_code == 201
    for _ in range(2):
        response = client.post("/join_project", json={"userId": "u2", "projectId": "p1"})
        assert response.status_code == 200
        assert response.get_json()["members"] == ["u1", "u2"]
    snapshot = read_database(database)
    assert snapshot["users"][1]["projects"] == ["p1"]
    assert snapshot["projects"][0]["members"] == ["u1", "u2"]
    assert client.get("/get_user_projects_list/u2").get_json() == snapshot["projects"]


@pytest.mark.parametrize("data,status", [
    ({"userId": "missing", "projectId": "p1"}, 404),
    ({"userId": "u1", "projectId": "missing"}, 404),
    ({"projectId": "p1"}, 400),
    ({"userId": "u1"}, 400),
])
def test_invalid_join_does_not_change_database(client, project, database, data, status):
    before = read_database(database)
    assert client.post("/join_project", json=data).status_code == status
    assert read_database(database) == before


@pytest.mark.parametrize("method", ["get", "post"])
def test_project_lookup_and_user_projects(client, project, method):
    assert project["description"] == ""
    if method == "get":
        detail = client.get("/get_project_info/p1")
        listing = client.get("/get_user_projects_list/u1")
    else:
        detail = client.post("/get_project_info", json={"projectId": "p1"})
        listing = client.post("/get_user_projects_list", json={"userId": "u1"})
    assert detail.status_code == listing.status_code == 200
    assert detail.get_json() == project
    assert listing.get_json() == [project]


@pytest.mark.parametrize("endpoint", ["get_project_info", "get_user_projects_list"])
def test_lookup_rejects_unknown_id_or_missing_id(client, endpoint):
    assert client.get(f"/{endpoint}/missing").status_code == 404
    field = "projectId" if endpoint == "get_project_info" else "userId"
    assert client.post(f"/{endpoint}", json={field: "missing"}).status_code == 404
    assert client.post(f"/{endpoint}", json={}).status_code == 400


def test_new_user_has_no_projects(client, owner):
    response = client.get("/get_user_projects_list/u1")
    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize("credentials", [
    {"username": "alice", "password": {"$ne": ""}},
    {"username": {"$ne": ""}, "password": {"$ne": ""}},
])
def test_login_rejects_query_operators(client, owner, credentials):
    """A MongoDB operator in place of a password must not match any user."""
    response = client.post("/login", json=credentials)
    assert response.status_code == 401
    assert response.get_json() == {"error": "invalid username or password"}
