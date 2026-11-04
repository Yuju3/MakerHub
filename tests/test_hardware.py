"""Regression tests for hardware sets, check-out, and check-in."""

import pytest

import hardwareDatabase


@pytest.fixture
def hardware(client):
    for name, capacity in [("HWSet1", 100), ("HWSet2", 50)]:
        response = client.post("/create_hardware_set", json={"hwName": name, "capacity": capacity})
        assert response.status_code == 201


@pytest.fixture
def member(client, project):
    """A second user who has joined the owner's project."""
    user = {"username": "bob", "userId": "u2", "password": "secret"}
    assert client.post("/add_user", json=user).status_code == 201
    assert client.post("/join_project", json={"userId": "u2", "projectId": "p1"}).status_code == 200
    return user


def check_out(client, quantity, hw="HWSet1", project="p1", user="u1"):
    return client.post("/check_out", json={
        "projectId": project, "hwName": hw, "quantity": quantity, "userId": user,
    })


def check_in(client, quantity, hw="HWSet1", project="p1", user="u1"):
    return client.post("/check_in", json={
        "projectId": project, "hwName": hw, "quantity": quantity, "userId": user,
    })


def availability(client, hw="HWSet1"):
    return client.get(f"/get_hw_info/{hw}").get_json()["availability"]


def usage(client, hw="HWSet1", project="p1"):
    return client.get(f"/get_project_info/{project}").get_json()["hwUsage"].get(hw, 0)


# ------------------------------------------------------------ hardware sets


def test_new_set_starts_fully_available(client):
    response = client.post("/create_hardware_set", json={"hwName": "HWSet1", "capacity": 100})
    assert response.status_code == 201
    assert response.get_json() == {"hwName": "HWSet1", "capacity": 100, "availability": 100}


def test_list_hardware_sets_and_names(client, hardware):
    assert client.get("/get_all_hw_names").get_json() == ["HWSet1", "HWSet2"]
    assert client.get("/get_all_hw").get_json() == [
        {"hwName": "HWSet1", "capacity": 100, "availability": 100},
        {"hwName": "HWSet2", "capacity": 50, "availability": 50},
    ]


def test_hardware_info_by_get_and_post(client, hardware):
    expected = {"hwName": "HWSet2", "capacity": 50, "availability": 50}
    assert client.get("/get_hw_info/HWSet2").get_json() == expected
    assert client.post("/get_hw_info", json={"hwName": "HWSet2"}).get_json() == expected
    assert client.get("/get_hw_info/missing").status_code == 404
    assert client.post("/get_hw_info", json={}).status_code == 400


def test_duplicate_set_is_rejected(client, hardware):
    response = client.post("/create_hardware_set", json={"hwName": "HWSet1", "capacity": 5})
    assert response.status_code == 409
    assert client.get("/get_hw_info/HWSet1").get_json()["capacity"] == 100


@pytest.mark.parametrize("data", [
    {"hwName": "HWSet3"},
    {"hwName": "HWSet3", "capacity": 0},
    {"hwName": "HWSet3", "capacity": -5},
    {"hwName": "HWSet3", "capacity": 2.5},
    {"hwName": "HWSet3", "capacity": "10"},
    {"hwName": "HWSet3", "capacity": True},
    {"hwName": "bad.name", "capacity": 10},
    {"hwName": "$bad", "capacity": 10},
    {"capacity": 10},
])
def test_invalid_set_is_rejected(client, data):
    assert client.post("/create_hardware_set", json=data).status_code == 400
    assert client.get("/get_all_hw").get_json() == []


# ---------------------------------------------------------------- check-out


def test_check_out_moves_units_to_project(client, project, hardware):
    response = check_out(client, 30)
    assert response.status_code == 200
    body = response.get_json()
    assert body["quantity"] == 30
    assert body["projectUsage"] == 30
    assert body["hardware"] == {"hwName": "HWSet1", "capacity": 100, "availability": 70}
    assert availability(client) == 70
    assert usage(client) == 30


def test_repeated_check_outs_add_up(client, project, hardware):
    check_out(client, 10)
    check_out(client, 15)
    assert usage(client) == 25
    assert availability(client) == 75


def test_request_beyond_availability_gets_what_is_left(client, project, hardware):
    check_out(client, 40, hw="HWSet2")
    response = check_out(client, 25, hw="HWSet2")
    assert response.status_code == 200
    body = response.get_json()
    assert body["quantity"] == 10
    assert "only 10 of 25" in body["message"]
    assert availability(client, "HWSet2") == 0
    assert usage(client, "HWSet2") == 50


def test_check_out_from_empty_set_changes_nothing(client, project, hardware):
    check_out(client, 50, hw="HWSet2")
    response = check_out(client, 1, hw="HWSet2")
    assert response.status_code == 409
    assert availability(client, "HWSet2") == 0
    assert usage(client, "HWSet2") == 50


def test_sets_are_tracked_separately(client, project, hardware):
    check_out(client, 10, hw="HWSet1")
    check_out(client, 5, hw="HWSet2")
    project_info = client.get("/get_project_info/p1").get_json()
    assert project_info["hwUsage"] == {"HWSet1": 10, "HWSet2": 5}
    assert availability(client, "HWSet1") == 90
    assert availability(client, "HWSet2") == 45


def test_projects_share_the_same_pool(client, project, hardware):
    assert client.post("/create_project", json={
        "projectId": "p2", "name": "Drone", "ownerId": "u1",
    }).status_code == 201
    check_out(client, 60, project="p1")
    response = check_out(client, 60, project="p2")
    assert response.get_json()["quantity"] == 40
    assert usage(client, project="p1") == 60
    assert usage(client, project="p2") == 40
    assert availability(client) == 0


# ----------------------------------------------------------------- check-in


def test_check_in_returns_units(client, project, hardware):
    check_out(client, 30)
    response = check_in(client, 12)
    assert response.status_code == 200
    assert response.get_json()["projectUsage"] == 18
    assert availability(client) == 82
    assert usage(client) == 18


def test_cannot_check_in_more_than_project_holds(client, project, hardware):
    check_out(client, 5)
    response = check_in(client, 6)
    assert response.status_code == 409
    assert "only has 5" in response.get_json()["error"]
    assert availability(client) == 95
    assert usage(client) == 5


def test_cannot_check_in_another_projects_units(client, project, hardware):
    client.post("/create_project", json={"projectId": "p2", "name": "Drone", "ownerId": "u1"})
    check_out(client, 20, project="p1")
    assert check_in(client, 1, project="p2").status_code == 409
    assert availability(client) == 80


def test_any_member_can_return_project_units(client, member, hardware):
    check_out(client, 10, user="u1")
    assert check_in(client, 10, user="u2").status_code == 200
    assert availability(client) == 100
    assert usage(client) == 0


# --------------------------------------------------------- invalid requests


@pytest.mark.parametrize("operation", [check_out, check_in])
@pytest.mark.parametrize("quantity", [0, -3, 2.5, "5", True, None])
def test_quantity_must_be_positive_whole_number(client, project, hardware, operation, quantity):
    assert operation(client, quantity).status_code == 400
    assert availability(client) == 100


@pytest.mark.parametrize("operation", [check_out, check_in])
def test_non_members_are_refused(client, project, hardware, operation):
    client.post("/add_user", json={"username": "eve", "userId": "u3", "password": "x"})
    assert operation(client, 1, user="u3").status_code == 403
    assert availability(client) == 100


@pytest.mark.parametrize("operation", [check_out, check_in])
@pytest.mark.parametrize("target", [{"project": "missing"}, {"hw": "missing"}])
def test_unknown_project_or_set_is_not_found(client, project, hardware, operation, target):
    assert operation(client, 1, **target).status_code == 404


@pytest.mark.parametrize("missing", ["projectId", "hwName", "userId"])
def test_check_out_requires_fields(client, project, hardware, missing):
    data = {"projectId": "p1", "hwName": "HWSet1", "quantity": 1, "userId": "u1"}
    del data[missing]
    assert client.post("/check_out", json=data).status_code == 400


def test_check_out_rejects_query_operators(client, project, hardware):
    response = client.post("/check_out", json={
        "projectId": {"$ne": ""}, "hwName": "HWSet1", "quantity": 1, "userId": "u1",
    })
    assert response.status_code == 400
    assert availability(client) == 100


# ------------------------------------------------- storage-level guarantees


def test_request_space_never_goes_below_zero(database):
    hardwareDatabase.createHardwareSet(database, "HWSet1", 10)
    assert hardwareDatabase.requestSpace(database, "HWSet1", 4) == 4
    assert hardwareDatabase.requestSpace(database, "HWSet1", 20) == 6
    assert hardwareDatabase.requestSpace(database, "HWSet1", 1) == 0
    assert hardwareDatabase.queryHardwareSet(database, "HWSet1")["availability"] == 0


def test_return_space_never_exceeds_capacity(database):
    hardwareDatabase.createHardwareSet(database, "HWSet1", 10)
    assert hardwareDatabase.returnSpace(database, "HWSet1", 1) is False
    assert hardwareDatabase.queryHardwareSet(database, "HWSet1")["availability"] == 10


def test_update_availability_stays_in_range(database):
    hardwareDatabase.createHardwareSet(database, "HWSet1", 10)
    assert hardwareDatabase.updateAvailability(database, "HWSet1", 11) is False
    assert hardwareDatabase.updateAvailability(database, "HWSet1", -1) is False
    assert hardwareDatabase.updateAvailability(database, "HWSet1", 7) is True
    assert hardwareDatabase.queryHardwareSet(database, "HWSet1")["availability"] == 7


def test_old_projects_without_usage_still_work(client, database, owner, hardware):
    # Projects seeded before hardware tracking existed have no hwUsage field.
    database.projects.insert_one({
        "projectId": "old", "name": "Old", "description": "", "ownerId": "u1", "members": ["u1"],
    })
    assert client.get("/get_project_info/old").get_json()["hwUsage"] == {}
    assert check_out(client, 3, project="old").status_code == 200
    assert usage(client, project="old") == 3


def test_request_space_retries_when_another_request_got_there_first(database, monkeypatch):
    """Simulate a race: our read says 10 are available, but another request
    already took 7. The conditional update must refuse the stale amount and
    retry with the real availability instead of going negative."""
    hardwareDatabase.createHardwareSet(database, "HWSet1", 10)
    database.hardwareSets.update_one({"hwName": "HWSet1"}, {"$set": {"availability": 3}})
    real_query = hardwareDatabase.queryHardwareSet
    stale_reads = [{"hwName": "HWSet1", "capacity": 10, "availability": 10}]
    monkeypatch.setattr(
        hardwareDatabase, "queryHardwareSet",
        lambda db, name: stale_reads.pop() if stale_reads else real_query(db, name),
    )
    assert hardwareDatabase.requestSpace(database, "HWSet1", 10) == 3
    assert real_query(database, "HWSet1")["availability"] == 0
