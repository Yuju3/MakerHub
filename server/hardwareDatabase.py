from pymongo import MongoClient

DB_NAME = "HardwareCheckout"
COLLECTION_NAME = "HardwareSets"


def createHardwareSet(client, hwSetName, initCapacity):
    if not isinstance(hwSetName, str) or not hwSetName.strip():
        raise ValueError("Hardware name cannot be empty")

    if type(initCapacity) is not int or initCapacity < 0:
        raise ValueError("Capacity must be a non-negative integer")

    collection = client[DB_NAME][COLLECTION_NAME]

    if collection.find_one({"hwName": hwSetName}):
        raise ValueError("Hardware set already exists")

    hardware = {
        "hwName": hwSetName,
        "capacity": initCapacity,
        "availability": initCapacity
    }

    collection.insert_one(hardware)
    return hardware


def queryHardwareSet(client, hwSetName):
    collection = client[DB_NAME][COLLECTION_NAME]
    return collection.find_one({"hwName": hwSetName})


def updateAvailability(client, hwSetName, newAvailability):
    pass


def requestSpace(client, hwSetName, amount):
    pass


def getAllHwNames(client):
    collection = client[DB_NAME][COLLECTION_NAME]
    return [
        hardware["hwName"]
        for hardware in collection.find({}, {"hwName": 1})
    ]