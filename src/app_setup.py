"""Envoy data simulator flask setup."""

import logging
import logging.handlers
import os
from typing import Any

from dotenv import load_dotenv, set_key

from models.envoy_model import EnvoySim

DATA_DIR = "./data"
ENV_FILE = f"{DATA_DIR}/envoy_container.env"
LOG_FILE = f"{DATA_DIR}/envoy_container.log"

logger = logging.getLogger(__name__)


def app_setup() -> dict[str, Any]:
    """Prepare app for running, before flask application creation."""
    env: dict[str, Any] = {}  # store env variables

    # Ensure data directory exists so log file can be written
    os.makedirs(DATA_DIR + "/fixtures", exist_ok=True)

    # load environment variables and overrides from container volume
    load_dotenv(ENV_FILE, override=True)

    # Build out environment variables
    env["debug"] = os.getenv("DEBUG", "False").lower() in ("true", "1", "t", "y", "yes")
    env["dev"] = os.getenv("MODE", "Production").lower() in (
        "development",
        "d",
        "dev",
        "test",
        "t",
    )
    env["fixture"] = os.environ.get("FIXTURE", "")
    env["serial"] = os.environ.get("ENVOY_SERIAL", "1234456789012")
    env["host"] = os.environ.get("HOST", "0.0.0.0")  # noqa: S104
    env["port"] = 443
    env["JSON_SORT_KEYS"] = False
    # Set this ASYNC_MODE to None, "threading", "eventlet" or "gevent"
    env["async"] = os.environ.get("ASYNC_MODE")
    env["cert"] = os.environ.get("CERT", "adhoc")
    env["key"] = os.environ.get("KEY")

    # setup log handlers and logging configuration
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=(1048576 * 5), backupCount=7
    )
    console_handler = logging.StreamHandler()  # output to container console

    logging.basicConfig(
        handlers=[file_handler, console_handler],
        format="%(asctime)s "
        + "%(levelname)s "
        + "[%(name)s-%(funcName)s: %(lineno)d ] "
        + "%(message)s",
        level=logging.DEBUG if env["debug"] else logging.INFO,
    )

    logger.info("Starting Envoy Data Simulator")
    for var, setting in env.items():
        logger.info(f"{var}: {setting}")

    # don't log this one
    # python -c 'import secrets; print(secrets.token_hex())'
    env["SECRET_KEY"] = os.environ.get("SECRET_KEY", "this2sthes2cr3ttOus4!")

    # create our simulation data model and load all data
    envoy_sim: EnvoySim = EnvoySim(
        path=env["fixture"], serial=env["serial"], data_path=DATA_DIR
    )
    env["sim"] = envoy_sim
    envoy_sim.start_sim()

    return env


def env_update(settings: dict[str, Any]) -> None:
    """Appened new variable to env file."""
    for key, value in settings.items():
        set_key(ENV_FILE, key, value)
