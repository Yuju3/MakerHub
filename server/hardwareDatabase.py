"""Hardware set operations backed by the MongoDB `hardwareSets` collection.

Hardware set document:
{
    "hwName": str,         # e.g. "HWSet1"; unique
    "capacity": int,       # total units the makerspace owns
    "availability": int    # units not currently checked out
}

availability always stays between 0 and capacity. Every change to it is a
single conditional update inside MongoDB, so two people checking out at the
same moment can never take more units than exist.
"""

from pymongo.errors import DuplicateKeyError

NO_ID = {"_id": 0}


def createHardwareSet(db, hwSetName, initCapacity):
    """Add a new hardware set with every unit available. Returns None if the name is taken."""
    hw_set = {"hwName": hwSetName, "capacity": initCapacity, "availability": initCapacity}
    try:
        db.hardwareSets.insert_one(hw_set)
    except DuplicateKeyError:
        return None
    return queryHardwareSet(db, hwSetName)


def queryHardwareSet(db, hwSetName):
    return db.hardwareSets.find_one({"hwName": hwSetName}, NO_ID)


def getAllHardwareSets(db):
    """Capacity and availability of every set, sorted by name."""
    return list(db.hardwareSets.find({}, NO_ID).sort("hwName", 1))


def getAllHwNames(db):
    return [hw["hwName"] for hw in getAllHardwareSets(db)]


def updateAvailability(db, hwSetName, newAvailability):
    """Set availability directly (an admin correction). Refuses values outside 0..capacity."""
    result = db.hardwareSets.update_one(
        {"hwName": hwSetName, "capacity": {"$gte": newAvailability}},
        {"$set": {"availability": newAvailability}},
    ) if newAvailability >= 0 else None
    return bool(result and result.matched_count)


def requestSpace(db, hwSetName, amount, max_attempts=5):
    """Take up to `amount` units out of a set and return how many were granted.

    If fewer units are available than requested, grants what is left
    (possibly 0). The update only applies while availability is still at
    least the granted amount; if another request took units in between,
    nothing changes and we retry with the new availability.
    """
    for _ in range(max_attempts):
        hw_set = queryHardwareSet(db, hwSetName)
        if hw_set is None:
            return 0
        granted = min(amount, hw_set["availability"])
        if granted <= 0:
            return 0
        result = db.hardwareSets.update_one(
            {"hwName": hwSetName, "availability": {"$gte": granted}},
            {"$inc": {"availability": -granted}},
        )
        if result.modified_count:
            return granted
    return 0


def returnSpace(db, hwSetName, amount):
    """Put `amount` units back. Only applies if it keeps availability within capacity."""
    result = db.hardwareSets.update_one(
        {"hwName": hwSetName, "$expr": {"$lte": [{"$add": ["$availability", amount]}, "$capacity"]}},
        {"$inc": {"availability": amount}},
    )
    return bool(result.modified_count)
