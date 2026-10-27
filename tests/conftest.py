"""Give every API test its own database instead of changing application data."""

import json

import pytest

import app as backend


@pytest.fixture
def database_file(tmp_path, monkeypatch):
    path = tmp_path / "database.json"
    path.write_text(json.dumps({"users": [], "projects": []}), encoding="utf-8")
    monkeypatch.setattr(backend, "DATABASE_FILE", path)
    return path


@pytest.fixture
def client(database_file, monkeypatch):
    monkeypatch.setitem(backend.app.config, "TESTING", True)
    with backend.app.test_client() as client:
        yield client


@pytest.fixture
def owner(client):
    user = {"username": "alice", "userId": "u1", "password": "test-password"}
    assert client.post("/add_user", json=user).status_code == 201
    return user


@pytest.fixture
def project(client, owner):
    data = {"projectId": "p1", "name": "Robot", "ownerId": owner["userId"]}
    response = client.post("/create_project", json=data)
    assert response.status_code == 201
    return response.get_json()
