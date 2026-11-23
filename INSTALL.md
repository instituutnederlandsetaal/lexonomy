# Local installation

## Docker Compose

From the repository root, build and start Lexonomy.

```sh
docker compose up --build -d
docker compose logs lexonomy
```

Open [http://localhost:8000/](http://localhost:8000/). With the default configuration and a fresh database, the logs show a **Lexonomy setup code**. Enter it on the setup screen and choose a password for `root@localhost`. Use the most recent code if the container restarted before setup finished. `docker compose down` stops Lexonomy and keeps its database in the `lexonomy_data` volume.

Set `VER` when building to use a different image tag and display version. The default is `dev`.

Run this command to reset the password for an existing account.

```sh
docker compose exec lexonomy python adminscripts/changePassword.py root@localhost
```

The command prints the new password. In the development stack, use `docker compose -f docker-compose.dev.yml exec backend` in place of `docker compose exec lexonomy`.

## Frontend development

Use Node.js 22.12 or newer. From the repository root, run the frontend tools in `frontend/`.

```sh
cd frontend
npm ci
npm start
```

Open [http://localhost:5173/](http://localhost:5173/). Vite applies Vue changes as you save and provides a local API URL in the HTML. It proxies that URL to `http://127.0.0.1:8000` by default. Start the Python backend separately using the source installation steps below, or set `LEXONOMY_BACKEND_URL` to the API root of a running installation.

```sh
LEXONOMY_BACKEND_URL=http://127.0.0.1:9000 npm start
LEXONOMY_BACKEND_URL=https://lexonomy.example.org/lexonomy/ npm start
```

The target can include a path. The browser sends login, edits, imports, and other requests through the dev server to that target. If you point at production, writes affect production data.

### Docker development

From the repository root, start the Python backend and Vite together.

```sh
docker compose -f docker-compose.dev.yml up --build
```

Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/). On first startup, use the setup code from the backend logs to create `root@localhost`. Both containers load the local source with live reload. The dev stack uses its own SQLite volume. Set `FRONTEND_PORT` to change the published port.

To use another installation, start just the frontend service and set the backend URL. Inside Docker, use `host.docker.internal` to reach a service exposed on the Docker host.

```sh
LEXONOMY_BACKEND_URL=http://host.docker.internal:8000 docker compose -f docker-compose.dev.yml up frontend
LEXONOMY_BACKEND_URL=https://lexonomy.example.org/lexonomy/ docker compose -f docker-compose.dev.yml up frontend
```

## Install from source

Install uv and use Node.js 22.12 or newer. The commands below select Python 3.12. PyICU requires ICU development libraries, `pkg-config`, and a C++ compiler when it builds from source. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

```sh
cd api
uv venv --python 3.12
. .venv/bin/activate
uv pip install -r requirements.txt

cd ../frontend
npm ci
npm run build
```

Vite writes the production site to `frontend/dist/`. It hashes bundled files and copies the guide and licence icons from `frontend/public/` at stable URLs. Bottle serves the build and the API from the same origin. You can skip the build if you only use the Vite dev server.

## Configuration

Configuration uses `config/siteconfig.json` when present. Comments (`//` and `/* */`) are allowed.
When missing, Lexonomy uses the example configuration file `config/siteconfig.example.json`.
Copy the example file to `config/siteconfig.json` before editing. 

```sh
cp config/siteconfig.example.json config/siteconfig.json
```

After editing the file, restart the running service to apply it.

```sh
docker compose restart lexonomy
# Development stack
docker compose -f docker-compose.dev.yml restart backend
```

To change the config name or location, use environment variable `LEXONOMY_SITECONFIG`.
The production docker stack forwards this env var directly, the development stack instead forwards `LEXONOMY_DEV_SITECONFIG` as `LEXONOMY_SITECONFIG` inside the container.
When running on the host, you should therefor use `LEXONOMY_SITECONFIG` to point to your configuration file (if you don't want to use the `config/` directory).

### Server, client, and API URLs

All three settings are optional.

- `serverUrl` tells Lexonomy where to listen for HTTP requests and under which path to serve the site and API. It defaults to `0.0.0.0:8000/`, which means all network interfaces, port 8000, and the root path. If you give only a path, Lexonomy uses the default host and port.
- `clientUrl` is the public address Lexonomy uses in emails and exported entry links. If you leave it out or set it to `""`, Lexonomy uses `http://` with the host, port, and path from `serverUrl`, replacing `0.0.0.0` with `localhost`. If you give only a path, it uses `http://localhost:8000` with that path.
- `apiUrl` tells the browser where to send API requests. Use a path starting with `/` to send requests to the same origin that served the page. This lets you test on a local domain while keeping `clientUrl` set to the public domain. You can also specify a full HTTP(S) URL. If you leave `apiUrl` out or set it to `""`, the browser uses `clientUrl`.

| `serverUrl` | `clientUrl` | `apiUrl` | Where Lexonomy listens | Browser API root |
| --- | --- | --- | --- | --- |
| Omitted | Omitted | Omitted | `0.0.0.0:8000/` | `http://localhost:8000/` |
| `"/lexonomy/"` | `""` | Omitted | `0.0.0.0:8000/lexonomy/` | `http://localhost:8000/lexonomy/` |
| `"0.0.0.0:9000/lexonomy/"` | Omitted | Omitted | `0.0.0.0:9000/lexonomy/` | `http://localhost:9000/lexonomy/` |
| `"/"` | `"https://example.org/lexonomy/"` | Omitted | `0.0.0.0:8000/` | `https://example.org/lexonomy/` |
| `"/"` | `"https://example.org/lexonomy/"` | `"/lexonomy/"` | `0.0.0.0:8000/` | `/lexonomy/` on the page's origin |

In the last two examples, the proxy removes `/lexonomy/` when forwarding requests to Lexonomy. If the proxy keeps that prefix, set `serverUrl` to `"/lexonomy/"` as well. Redirect `/lexonomy` to `/lexonomy/` at the proxy and serve both the site and API at that prefix.

When Vite serves the page during development, set `LEXONOMY_BACKEND_URL` to the API root Vite should forward requests to. It defaults to `http://127.0.0.1:8000` when you run Vite locally. [Frontend development](#frontend-development)

Docker Compose publishes port 8000 by default. If you change the listen port in `serverUrl`, update the container side of the port mapping. If you change the published address, update `clientUrl`.

When upgrading, move the old `baseUrl` value to `clientUrl` and put the backend's bind host, port and old `rootPath` into `serverUrl`. Until you do, Lexonomy reads the old fields as fallbacks. Move any bind address previously passed on the command line into `serverUrl`.

### Data directory

```js
"dataDir": "../data/"
```

This is the path to the `data` folder where Lexonomy will store all its data, including (importantly) all the dictionaries. Note that the directory name does not have to be `data`, it can be anything you want.

Relative paths start in `api/`, or `/opt/service/api` in Docker. You can also use an absolute path such as `/home/joebloggs/lexonomydata/`.

Upon start, Lexonomy creates three subdirectories automatically:

- `dicts` – a directory with individual dictionaries, each being an SQLite database,
- `uploads` – a directory for temporary storage of user-uploaded imports,
- `sqlite_tmp` – a directory that SQLite will use as its temporary directory.

### Logging

```js
"verbose": false
```

If you set this to `true` Lexonomy will report each HTTP request (except requests for static files) to standard error output (= to the command line or terminal) – useful for debugging.

### Welcome message

```js
"welcome": "Welcome to your <a href='http://www.lexonomy.eu/'>Lexonomy</a> installation."
```

The current login page ignores this legacy setting.

### Admin accounts

```js
"admins": ["root@localhost"]
```

Accounts listed here can administer the installation. Browser setup creates `root@localhost` when that address is configured and the database has no administrator. For other configured admin addresses, the initializer creates missing accounts and prints their initial passwords.

## Start a source installation

From `api/`, initialize and upgrade the databases, then start the server.

```sh
python3 adminscripts/init.py
python3 adminscripts/updates.py
python3 migrate.py
python3 lexonomy.py
```

Open [http://localhost:8000/](http://localhost:8000/) with the default configuration. Enter the setup code printed by the initializer to create `root@localhost`. For subsequent upgrades, rebuild the frontend and run the same startup commands. Docker runs the database scripts before starting the server.

Accounts created through Sketch Engine can set a local password through **Forgot password?** when email is configured. An administrator with server access can also set a password with `python3 adminscripts/changePassword.py user@example.com` from `api/`.

## Run the tests

After installing the Python requirements, run the `test-*.py` scripts from `api/`. The database tests create their own temporary files. Run `npm test` from `frontend/` for the frontend tests.
