# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Build Docker image**
  ```bash
  docker build -t lab-flask-restplus-swagger .
  ```

- **Install dependencies**
  ```bash
  make install   # uses Poetry; creates a virtual environment and installs all packages
  ```

- **Lint code**
  ```bash
  make lint      # flake8 + pylint
  ```

- **Run tests**
  ```bash
  make test      # runs pytest on the entire test suite
  ```
  To run a single test file or method:
  ```bash
  pytest path/to/test_file.py::TestClass::test_method
  ```

- **Start the service locally**
  ```bash
  make run       # uses honcho to launch the Procfile (gunicorn)
  ```
  Or directly with gunicorn:
  ```bash
  gunicorn wsgi:app
  ```

- **Open in VSCode dev container** – The repository contains a `.devcontainer` configuration that sets up a Docker container with CouchDB. In VSCode, click the green “Remote Containers” icon and choose *Reopen in Container*.

## High‑Level Architecture

```
wsgi.py → create_app() (service/__init__.py)
    ├─ Config loaded from service/config.py (env vars: CLOUDANT_DBNAME, API_KEY, etc.)
    ├─ Routes defined in service/routes.py (Flask‑RESTX, Swagger at /apidocs)
    │   └─ CRUD endpoints for Pet resource
    ├─ Models in service/models.py (Pet class, Gender enum, Cloudant persistence)
    └─ Common utilities in service/common/ (status codes, error handlers, logging)
```

- **Database** – Uses IBM Cloudant / CouchDB. Connection parameters are read from environment variables (`CLOUDANT_HOST`, `CLOUDANT_PORT`, `CLOUDANT_USERNAME`, `CLOUDANT_PASSWORD`). In the dev container a local CouchDB instance is started automatically.

- **Authentication** – API key protected via `X‑Api-Key` header. Keys can be generated with `routes.generate_apikey()` and are stored in the Flask config (`API_KEY`).

- **Testing** – Tests are written with `pytest`. The test suite uses a factory (`tests/factories.py`) to generate fake Pet objects and interacts with the app through the Flask test client.

## Key Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLOUDANT_DBNAME` | Name of Cloudant database | `petshop` |
| `CLOUDANT_HOST` | Host for CouchDB/Cloudant | `localhost` |
| `CLOUDANT_PORT` | Port for CouchDB/Cloudant | (implied by env) |
| `CLOUDANT_USERNAME` | Username | `admin` |
| `CLOUDANT_PASSWORD` | Password | `pass` |
| `API_KEY` | Secret key used to authenticate API requests | not set by default; generated at runtime if missing |
| `FLASK_APP`, `FLASK_DEBUG` | Flask runtime settings (set in dev container) | `wsgi:app`, `"True"` |
| `PORT` | Port exposed for the service | `8080` |

## Important Files

- `service/__init__.py` – Application factory (`create_app`) and configuration loading.
- `service/routes.py` – API endpoints, Swagger documentation, authentication decorator.
- `service/models.py` – Pet model with Cloudant persistence logic.
- `wsgi.py` – WSGI entry point used by gunicorn.
- `Makefile` – Build, lint, test, run targets.
- `Procfile` – Process definition for honcho (gunicorn).
- `Dockerfile` – Production image build.
- `.devcontainer/` – Dev container configuration with CouchDB service.
