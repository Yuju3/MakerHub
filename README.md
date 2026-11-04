# MakerHub

MakerHub is a Hardware-as-a-Service (HaaS) proof of concept built for the ECE 461L team project at UT Austin. Students create an account, create or join projects, and check hardware sets (such as Arduino and Raspberry Pi kits) in and out against those projects, similar to how a campus makerspace lends equipment.

The stack is a **React** frontend, a **Flask** REST API, and a **MongoDB Atlas** database.

## Project status

| Feature | Status |
|---|---|
| Register, sign in, sign out | Done |
| Create a project | Done |
| Join an existing project by ID and see its collaborators | Done |
| User and project data stored in MongoDB Atlas | Done |
| Backend API tests (pytest) | Done (35 tests, run against an in-memory database) |
| Hardware sets stored in the database, with an API | Not started (`hardwareDatabase.py` is a stub) |
| Check-in / check-out screen using real data | Not started (`Checkout.js` uses mock data) |
| Encrypted user IDs and passwords | Not started (passwords are currently plain text) |
| Cloud deployment | Not started |
| Forgot password | Placeholder only |

## Repository layout

```
MakerHub/
├── client/                  React frontend (Create React App)
│   └── src/
│       ├── pages/           Login, registration, forgot password, user portal
│       └── components/      Navbar, project card, join project, collaborators,
│                            checkout, error card
├── server/                  Flask backend
│   ├── app.py               API routes
│   ├── db.py                MongoDB Atlas connection and unique indexes
│   ├── usersDatabase.py     User operations
│   ├── projectsDatabase.py  Project operations
│   ├── hardwareDatabase.py  Hardware set operations (not implemented yet)
│   ├── seed.py              Loads the test data in database.json into Atlas
│   ├── database.json        Seed data only; the app no longer reads it
│   └── .env.example         Template for your local settings
├── tests/                   pytest API tests
└── pytest.ini
```

## Getting started

### Prerequisites

- Python 3.10 or newer
- Node.js (LTS version)
- Access to the team's MongoDB Atlas cluster. Ask a teammate for the connection string, or see [Setting up Atlas](#setting-up-atlas) to create your own cluster.

### 1. Configure the backend

In the `server` folder, copy the settings template and open it:

```bash
cd server
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
```

Set `MONGODB_URI` to the Atlas connection string, with the real database password in place of `<db_password>`. **Never commit `.env`.** It is listed in `.gitignore` because it contains the database password.

| Variable | Purpose | Default |
|---|---|---|
| `MONGODB_URI` | Atlas connection string | none (required) |
| `MONGODB_DB` | Database name | `makerhub` |
| `FRONTEND_ORIGIN` | Origin allowed to call the API (CORS) | `http://localhost:3000` |

### 2. Run the backend

```bash
pip install -r requirements.txt
python seed.py     # only needed once per database; safe to rerun
python app.py
```

The API runs at `http://127.0.0.1:5000`. Open `http://127.0.0.1:5000/health` to confirm the database connection: it should report `"database": "connected"`.

### 3. Run the frontend

In a second terminal, leaving the backend running:

```bash
cd client
npm install        # first time only
npm start
```

The app opens at `http://localhost:3000`.

### Test accounts

`seed.py` creates two accounts:

| Username | Password | Projects |
|---|---|---|
| `abc123` | `password` | Project `123` ("test"), as owner |
| `def123` | `password` | Project `123`, as a member |

### Setting up Atlas

Only needed if you want your own cluster instead of the team's.

1. Create a free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas).
2. Under **Security → Database Access**, add a database user with the **Read and write to any database** role. Use a password with only letters and numbers, so it needs no encoding inside the connection string.
3. Under **Security → Network Access**, add `0.0.0.0/0` (allow access from anywhere). The app's eventual cloud host will not have a fixed IP address.
4. On the cluster, click **Connect → Drivers → Python** and copy the connection string into `server/.env`.

## Running the tests

From the repository root:

```bash
pip install -r server/requirements-dev.txt
python -m pytest
```

The tests cover registration, login, project creation, project lookup, and joining projects, including invalid input, duplicate records, and NoSQL injection attempts.

The tests don't need Atlas or a `.env` file. Each test runs against a fresh in-memory MongoDB stand-in ([mongomock](https://github.com/mongomock/mongomock)), so the team's real database is never touched.

## API reference

All request and response bodies are JSON. Errors return `{"error": "<message>"}` with the status codes listed below. Passwords are never included in responses.

Every text field must be a non-empty string. Other types are rejected (with `400`, or `401` for login), which prevents NoSQL injection: without this check, a value like `{"$ne": ""}` would be treated as a MongoDB query operator.

| Method | Route | Request body | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | none | `200` with database status | `503` database unreachable |
| POST | `/add_user` | `username`, `userId`, `password` | `201` new user | `400` missing field, `409` username or userId taken |
| POST | `/login` | `username`, `password` | `200` user | `401` wrong or missing credentials |
| POST | `/create_project` | `projectId`, `name`, `ownerId`, optional `description` | `201` new project | `400` missing field, `404` owner not found, `409` projectId taken |
| POST | `/join_project` | `userId`, `projectId` | `200` updated project | `400` missing field, `404` user or project not found |
| GET | `/get_user_projects_list/<userId>` | none | `200` list of the user's projects | `404` user not found |
| POST | `/get_user_projects_list` | `userId` | same as the GET version | `400`, `404` |
| GET | `/get_project_info/<projectId>` | none | `200` project | `404` project not found |
| POST | `/get_project_info` | `projectId` | same as the GET version | `400`, `404` |

Example:

```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "abc123", "password": "password"}'
```

```json
{"username": "abc123", "userId": "abc123", "projects": ["123"]}
```

## Data model

The database has three collections. Unique indexes on the ID fields make MongoDB itself reject duplicates.

**users**: `username` (unique), `userId` (unique), `password`, and `projects`, a list of project IDs.

**projects**: `projectId` (unique), `name`, `description`, `ownerId`, and `members`, a list of user IDs. A user's `projects` list and a project's `members` list are kept in sync when a project is created or joined.

**hardwareSets** (planned): `hwName` (unique), `capacity`, and `availability`.

## Design notes

**Storage is isolated behind database modules.** `app.py` handles HTTP concerns only, such as reading requests, validating input, and choosing status codes. All data access goes through `usersDatabase.py`, `projectsDatabase.py`, and `hardwareDatabase.py`, which share one connection from `db.py`. Because of this, moving from a JSON file to MongoDB changed only the storage modules, and the routes and frontend stayed the same.

**Updates happen inside the database.** Joining a project uses MongoDB's `$addToSet`, which adds an ID only if it is not already in the list. MongoDB applies it in a single step, so simultaneous requests cannot overwrite each other, and joining twice has no effect.

**Configuration comes from the environment.** The connection string and allowed frontend origin are read from environment variables, so the same code runs locally and on a cloud host without edits, and no credentials are stored in the repository.
