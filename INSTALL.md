# Local installation

## Docker Compose

From the repository root, build and start Lexonomy.

```sh
docker compose up --build -d
docker compose logs lexonomy
```

Open [http://localhost:8000/](http://localhost:8000/). On first startup, the logs show the generated password for `root@localhost`. `docker compose down` stops Lexonomy and keeps its database in the `lexonomy_data` volume.

Set `VER` when building to use a different image tag and display version. The default is `dev`.

## Install from source

Use Python 3.12 and Node.js 22 to match the Docker build. PyICU requires ICU development libraries, `pkg-config`, and a C++ compiler when it builds from source.

```sh
cd website
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp siteconfig.json.template siteconfig.json
cp config.js.template config.js
npm ci
npm --prefix editor ci
npm run build
```

The frontend build writes to `website/dist`. During development, `npm run watch` rebuilds Riot on changes and starts the graphical editor's dev server. Set `window.GRAPHICAL_EDITOR_WEBPACK_DEV_SERVER_URL` in `website/config.js` to use that server.

## Configuration

Set `window.API_URL` in `website/config.js` to the backend URL. It usually matches `baseUrl` in `website/siteconfig.json`. Set `LEXONOMY_SITECONFIG` to load a different backend configuration. To customize Compose, point its two configuration mounts at your own copies of the templates.

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

This is the port number at which Lexonomy listens for incoming HTTP requests.

### Data directory

```js
"dataDir": "../data/"
```

This is the path to the `data` folder where Lexonomy will store all its data, including (importantly) all the dictionaries. Note that the directory name does not have to be `data`, it can be anything you want.

If the path given here is relative, it is interpreted relatively to the web application's current directory (= the `website` directory). It can also be an absolute path, eg. `/home/joebloggs/lexonomydata/`.

Upon start, Lexonomy creates three subdirectories automatically:

- `dicts` – a directory with individual dictionaries, each being an SQLite database,
- `uploads` – a directory for temporary storage of user-uploaded imports,
- `sqlite_tmp` – a directory that SQLite will use as its temporary directory.

### Logging

```js
"verbose": false
```

If you set this to `true` Lexonomy will report each HTTP request (except requests for static files) to standard error output (= to the command line or terminal) – useful for debugging.

### Tracking code

```js
"trackingCode": ""
```

This is an HTML snippet which Lexonomy inserts into every public-facing web page. You can replace it with your own tracking code from Google Analytics, StatCounter or whatever other web analytics service you use, or leave it blank.

### Welcome message

```js
"welcome": "Welcome to your <a href='http://www.lexonomy.eu/'>Lexonomy</a> installation."
```

This is the welcome message displayed on the home page of your Lexonomy installation (left of the log-in box).

### Admin accounts

```js
"admins": ["root@localhost"]
```  

This is an array of one or more e-mail addresses. People listed here are administrators: they can access everything in Lexonomy (including other people's dictionaries) and, after they log in, they will see options to create/change/delete user accounts, which other users don't see. You probably want to change this to your own e-mail address, like `joebloggs@example.com`.

## Start a source installation

From `website`, create your configured `dataDir` and initialize the databases. The initialization script prints the passwords for newly created administrators.

```sh
mkdir -p ../data
python3 adminscripts/init.py
python3 adminscripts/updates.py
python3 migrate.py
python3 lexonomy.py
```

Open [http://localhost:8000/](http://localhost:8000/) with the default configuration. For subsequent upgrades, rebuild the frontend and run `adminscripts/updates.py` and `migrate.py` before restarting the server. Docker runs these steps on startup.

## Run the import tests

After installing the Python requirements, run `python3 test-import.py` from `website`. The tests create their own temporary databases.
