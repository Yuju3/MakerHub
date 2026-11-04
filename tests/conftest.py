"""Give every API test its own empty database instead of touching Atlas.

mongomock is an in-memory stand-in for MongoDB that understands the same
pymongo calls, so the backend code runs unchanged and nothing is written
to the team's real database.
"""

import mongomock
import pytest

import app as backend
import db


@pytest.fixture
def database(monkeypatch):
    test_db = mongomock.MongoClient()["makerhub_test"]
    db.ensure_indexes(test_db)
    # get_db() returns the cached database, so it never connects to Atlas.
    monkeypatch.setattr(db, "_db", test_db)
    return test_db


@pytest.fixture
def client(database, monkeypatch):
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
