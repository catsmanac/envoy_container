# Content

- [Simulator](#simulator)
- [Installation](#installation)
- [Setup](#setup)
- [UI](#ui)

# Simulator

This is an Enphase Envoy / IQ Gateway data simulator. It provides an Envoy API simulation with data from a set of fixture files. Build with [Flask](https://pypi.org/project/Flask/) and [Flask-socketIO](https://pypi.org/project/Flask-SocketIO/).

The simulator in no way resembles any internal part of a physical Envoy, but rather provides data from a set of fixture files. The API attempts to mimic the Envoy behavior, but is an approximation at best, as the API is not described in detail and differs between Envoy firmware versions. The intent is to use it for limited testing. Using the simulator compares to using pytest with fixture files, but offers end-to-end testing running the simulator in a container.

The provided data is static, as read from the fixture files. Fixture file data is loaded into the internal data model. Any PUT or POST data is updating the internal data model and returned in a subsequent GET requests. The data is reset to fixture file content at restart of the simulator or load of a different fixture file set.

The simulator has logic for various test scenarios, all added as the need was there. These can be controlled from the [UI](#ui).

[Back to content](#content)

# Installation

Clone the repository or download the zip file and unpak it to a folder. 

The container needs a volume mapped to `/app/data` where it will search for settings, create a log file and expect fixture files. Adding the volume can be done in 2 ways:

- Create a .env file in the same location as the docker-compose.yml file and add a line containing `DATA_VOLUME=<path-to-data-folder>`, for example `DATA_VOLUME=/dev/sim/data`
```
        # env vars used by docker compose.
        # volume path to map to /app/data
        DATA_VOLUME=/dev/sim/data
```

or

- Edit docker-compose.yml and replace `${DATA_VOLUME}` by the path to the data volume to be used, e.g. `/dev/sim/data`.
```yaml
    volumes:
      - /dev/sim/data:/app/data
      - /etc/localtime:/etc/localtime:ro
```


Now build the container using your favorite tools and the docker-compose.yml file. For example, docker compose and start it right away:
```
docker compose -f 'docker-compose.yml' up -d --build 'envoy_container'
```

[Back to content](#content)

# Setup

At first start, the container will prepare the data volume. It will create a `fixtures` folder where fixture file sets can be added and a log file named envoy_container.log. If you didn't start the container yet and want to add fixture file sets before first start, create the `fixtures` folder manually.

```
/data
 +-- /fixtures
 +-- envoy_container.log 
```

## Settings

The operation of the simulator can be configured using an environment variable file named `envoy_container.env`. Place it in the data folder. The following settings can be specified:

| Variable | Description |
|----------|-------------|
| ENVOY_SERIAL | Envoy serial number to use for simulator. Default is 123456789012. |
| FIXTURE | Folder name of default fixture file set to use. Folder must exist in /data/fixtures folder. Optional, fixture file set to use can be selected in the [UI](#ui).|
| CERT | Path to cert.pem file to use for [self-signed certificate](#certificate). For example ./data/cert.pem. Use `adhoc` for adhoc ssl context. |
| KEY | Path to key.pem file to use for [self-signed certificate](#certificate). For example ./data/key.pem. |
| DEBUG | When defined to `true` or `yes`, default logging mode is set to debug, otherwise to info. |
| MODE | When set to `development` the more detailed socketio logging is also enabled. Default is `production` with disabled socketio logging. |
| HOST | IP address to listen on. Defaults to 0.0.0.0. listening on all localhost addresses. |
| ASYNC_MODE | Socketio mode to use. If not specified will automically detect best mode. Values can be "threading", "eventlet" or "gevent". | 
| SECRET_KEY | Key to use for cookies signing. Optional, if not specified an internal key is used. 

Example environment variable file specifying the envoy serialnumber, default fixture file set and a [self-signed certificate](#certificate):

```
ENVOY_SERIAL=123456789012
FIXTURE=8.3.5289
CERT=./data/cert.pem
KEY=./data/key.pem
```

When fully configured, above example would need below files in the Data volume.
```
/data
 +-- /fixtures
 |    +--- /8.3.5289
 |          +--- fixturefile1
 |          +--- fixturefile2
 |          +
 |          +--- fixturefileN
 |
 +-- cert.pem
 +-- envoy_container.log
 +-- envoy_container.env
 +-- key.pem
```

### Fixture files

A fixture file is the data returned by a single Envoy endpoint. A fixture file set is a group of fixture files for the endpoints of interest. Each fixture file set is grouped in a folder named after the purpose of the set. It can be any name, as long as the fixture file set folder is located in the `/data/fixtures` folder.

The name of an individual fixture file must follow a rule driven by the Envoy endpoint name. Any `/` has to be replaced by a `_`. Arguments must be postfixed to the name separated by `_` and argument name and value must be separated by `_`. For example `/production.json?details=1` data should be in a fixture file named `production.json_details_1`. Likewise `/ivp/pdm/device_data` becomes `ivp_pdm_device_data`.

Which fixture files need to be in a fixture file set is fully driven by what you want to test. The [pyenphase](https://pypi.org/project/pyenphase/) library has a [set of test file fixtures](https://github.com/pyenphase/pyenphase/tree/main/tests/fixtures) that can be used with this simulator. Optionally copy one or more fixture file set folders to the /data/fixtures location. Be aware that these sets are build for the libraries testing purposes, some will be generic, others very specific. 

### Certificate

The simulator is accessible via https, like the physical Envoy device. By default is uses ad-hoc ssl-context which creates a self-signed certificate at each startup. That will work fine for the API and testing, provided your code does not verify the server certificate.

The simulator also provides a [user interface](#ui) at `/` with the same ssl context. This will cause your browser to kick-in and report a security issue after each (re-)start of the container.

Optionally the simulator can be configured with an external (self-signed) certificate that will reduce this nuisance. To use this feature, create a (self-signed) certicate and place the cert.pem and key.pem files in the data volume. To create a self-signed certificate use `openssl` (see the desciption in https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https).

```
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

[Back to content](#content)

# UI

The simulator offers a user interface accessible with your browser at the configured ip address. It provides options to configure the use of the simulator, view logs and inspect data in the internal data model or the actual fixture files. These are accessible in the tabs on the main page.

## Configuration

<img src="/src/static/configuration.png" alt="configuration screenshot" />

Provides status and options to select for the running simulator.

### Status fields

| Item | Description | Notes |
|------|-------------|-------|
| Verbose | Verbosity level for log tab from 0-2 | Use the `toggle verbosity` button to change it |
| Serial number | Envoy serial number in use | Default or as set in environment variables |
| Firmware version | Envoy firmware version as found in the fixture file `info` | |
| Fixture folder | Current active fixture fileset folder | As set in environment variables or manualy changed |
| Switch to fixture | Select a new fixture file set to use | Select fileset from pulldown and use `Switch` button to activate it. Simulator will reload with new fixture data. |

### Manual simulations

These allow manual control to simulate specific behavior to be tested.

| Item | Description | Notes |
|------|-------------|-------|
| JWT Authorized | Shows the JWT endpoint was used.| Only `/info` and `/home` endpoints can be accessed withouth authorization. For other endpoint API client must authorize with /auth/check_jwt. Toggle it to test unauthorized state.|
| Restarting | If non-zero a restart simulation is active.| The value is how many client requests are still needed to end a restarting simulation. Use the `restart` button to (de-)activate a restart. |
| Timeout sim | Will delay any reply by 5 minutes thus effectively triggering request timeouts. | Use the `toggle timeout` button to (de-)activate. The sleepers count shows how many requests are in this state. |
| Next req Status | Force selected status on all requests. | Use the `401`, `404` , `503` buttons to select a status to use and `clear` to end status forcing. |
| Empty Inverter Array | Return an empty inverter array for next /api/v1/production/inverters endpoint. | Use `Toggle empty array` button to (de-)activate. |
| Inverter Invalid json | Return malformed inverter json for next /api/v1/production/inverters endpoint. | Use `Toggle invalid json` button to (de-)activate. |
| Next tariff Status | Force selected status only for /lib/admin/tariff endpoint. | Use the `401`, `404` , `503` buttons to select a status to use and `clear` to end status forcing. |
| Sc sched invalid status | Return an invalid status 0 for /ivp/sc/sched endpoint. | Use `Toggle sc sched status 0` button to (de-)activate. |
| ActiveEim zero | return activeCount = 0 for Production eim for /production endpoint| Use `Toggle active eim 0 on/off` button to (de-)activate. |
| Variable Power | return power values with some variations so they change | Use `Toggle variable Power on/off` button to (de-)activate. |

### Build-in simulations

#### ACB Sleep state

When ACB sleep state is set or cleared, updating delay is simulated by only setting or clearing the sleep state flag on next get request, one battery at a time. With multiple batteries it may take multiple gets before all batteries show actual sleep state and aggregate reflects it.

## Log

<img src="/src/static/log.png" alt="log screenshot" />

Shows logging of the requests. Is controlled by the verbosity level.

| Verbosity | Details |
|-----------|---------|
| 0 | Shows all request endpoints received and their resulting status. |
| 1 | Also shows the content of the request reply returned to the API client. |
| 2 | Adds more detailed logs. |

Logs can also be acessed on the container console and the `envoy_container.log` file in the `/data` volume. These have more detail and track error details.

The `Copy log` button copies the log content to the clipboard.

## Cache

<img src="/src/static/cache.png" alt="cache screenshot" />

Shows the content of the internal data model. Fixture files are loaded into the model upon first request. The list may grow in time as more endpoints are requested. If an endpoint is not in the list it was not yet requested. To view the content of a fixture file in the cache, click it and it will show right next to the list. The content may differ from the fixture file if any PUT, POST or DELETE was send to the endpoint that updated the model data. The cache list will refresh each time a new fixture file is loaded. The `Refresh` button forces a refresh.

## Fixtures

<img src="/src/static/fixtures.png" alt="fixtures screenshot" />

Shows the fixture files in the active fixture file set. Fixture files set are located in the `/data/fixtures` folder. See [fixture files](#fixture-files) for a description of fixture file names. To view the content of a fixture file in the fixture file set, click it and it will show right next to the list. The `Refresh` button forces a refresh of the fixture files in case new files were added to the current active set.

[Back to content](#content)