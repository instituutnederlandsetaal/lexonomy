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

Open [http://localhost:5173/](http://localhost:5173/). Vite applies Vue changes as you save and proxies application requests to `http://127.0.0.1:8000` by default. Start the Python backend separately using the source installation steps below, or point Vite at a running installation.

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

Use Python 3.12 and Node.js 22.12 or newer. PyICU requires ICU development libraries, `pkg-config`, and a C++ compiler when it builds from source.

```sh
cd api
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt

cd ../frontend
npm ci
npm run build
```

Vite writes the production site to `frontend/dist/`. It hashes bundled files and copies the guide and licence icons from `frontend/public/` at stable URLs. Bottle serves the build and the API from the same origin. You can skip the build if you only use the Vite dev server.

## Configuration

Configuration uses `config/siteconfig.json` when present.
When missing, Lexonomy uses the example configuration file `config/siteconfig.example.json`.
Before editing the configuration, make a copy of the example file as `config/siteconfig.json` you shouldn't edit the template.

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

### Base URL

```js
"baseUrl": "http://localhost:8000/"
```

This is the URL at which your Lexonomy installation is visible to web browsers. For reasons we will not go into now, Lexonomy needs to know that this URL is.

- For Lexonomy's “home” installation this is `https://www.lexonomy.eu/`.

- For a default local installation this is `http://localhost:8000/`.

- If you are setting up your own installation on a web server somewhere then this should be any URL, such as `http://www.mylexonomy.com/`.

Make sure the path (ie. the final forward slash) is included. If your installation of Lexonomy is meant to be accessible from the Internet at a URL that contains a path, such as `http://www.example.com/mylexonomy/`, then make sure to include the path `/mylexonomy/` in the URL too.

### Root path

```js
"rootPath": "/"
```

This is the path at which Lexonomy listens for incoming HTTP requests on the server. Under normal circumstances this should be the same as the path at the end of your URL, for example `/` or `/mylexonomy/`. If, however, you have a proxy server which listens for HTTP requests at one URL and then forwards them to another, then the first URL should be the `baseUrl` and the second URL's path should be the `rootPath`.

### Port

```js
"port": 8000
```

This is the fallback listen port for a source installation when `baseUrl` has no explicit port. Docker listens on port 8000 inside the container. To change the external port, change the published port in Compose and update `baseUrl`.

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

After installing the Python requirements, run `python3 test-import.py` and `python3 test-initial-admin.py` from `api/`. Both suites create their own temporary databases.
