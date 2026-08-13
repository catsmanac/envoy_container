"""Envoy data simulator utility functions."""

import asyncio
import logging
import os

from awesomeversion import AwesomeVersion
from flask import abort, current_app, request
from flask_socketio import emit  # type: ignore

from models.envoy_model import EnvoySim

DATA_DIR = "./data"
ENV_FILE = f"{DATA_DIR}/envoy_container.env"
LOG_FILE = f"{DATA_DIR}/envoy_container.log"

logger = logging.getLogger(__name__)


def getsim() -> EnvoySim | None:
    """Return envoy sim stored in application config."""
    sim: EnvoySim | None = current_app.config.get("sim")  # type: ignore
    return sim  # type: ignore


def sim_paths() -> list[str]:
    """Build list of fixture folder names in ./data."""
    sim = getsim()
    if not sim:
        return []
    try:
        fixtures = [f.name for f in os.scandir(sim.fixture_home()) if f.is_dir()]
    except FileNotFoundError:
        fixtures = []
    fixtures.sort()
    return fixtures


def route_to_file() -> str:
    """Map route to filename."""
    # replace all / by _
    file: str = request.path[1:].replace("/", "_")
    # add argument name and values
    for arg, val in request.args.items():
        file += f"_{arg}_{val}"
    return file


def emit_log(log_text: str, logit: bool = False):
    """Add line to log tab log viewer and application logger."""
    emit("logger", {"data": log_text}, broadcast=True, namespace="/")
    if logit:
        current_app.logger.info(log_text)


def update_index():
    """Send updates from simulation data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        return
    emit(
        "updateElement",
        {
            "serial_value": f"{sim.serial}",
            "firmware_value": f"{sim.firmware}",
            "path_value": f"{sim.path}",
            "authorized_value_value": f"{sim.authorized()} ({sim.auth_count})",
            "verbosity_value": f"{sim.verbosity}",
            "envoy_cycling_value": f"{sim.envoy_cycling}",
            "timeoutsim_value": f"{sim.timeoutsim}",
            "sleepers_value": f"sleepers: {sim.sleepers}",
            "next_request_status_value": f"{sim.next_request_status}",
            "empty_inverter_array_value": f"{sim.empty_inverter_array}",
            "invalid_json_value": f"{sim.invalid_json}",
            "next_tariff_status_value": f"{sim.next_tariff_status}",
            "sc_sched_status_0_value": f"{sim.sc_sched_status_0}",
            "active_eim_0_value": f"{sim.active_eim_0}",
            "variable_power_value": f"{sim.variable_power}",
            "store_ct_ph_1_0_value": f"{sim.store_ct_ph_1_0}",
        },
        broadcast=True,
        namespace="/",
    )


def full_path():
    """Full route name with arguments appended"""
    endpoint = request.path
    # add argument name and values
    for arg, val in request.args.items():
        endpoint += f"_{arg}_{val}"
    return endpoint


async def before_requests():
    """Before each request gets processed."""
    route = request.path
    endpoint = full_path()

    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.warning(f"before request no sim loaded {endpoint}")
        abort(503, description=f"before request no sim loaded {endpoint}")
    if sim.verbosity > 1:
        emit_log(f"before request {endpoint}", logit=True)

    # if HTTPS and not authorized only let /info and /home pass
    # others get 404 till authorized by calling "auth/check_jwt"
    matches = ["/info", "/home", "/auth/check_jwt", "/favicon.ico"]
    if not sim.authorized() and (all(x not in route for x in matches)):
        emit_log(f"unauthorized request {route}", logit=True)
        abort(401)

    # if cycle envoy simulation is active return 503.
    # except for v3 api_v1_productio, in this case
    # reply with zero values during envoy restart
    if sim.envoy_cycling > 0 and not (
        route == "api_v1_production" and AwesomeVersion(sim.firmware).major == "3"
    ):
        # simulate not avaialble
        emit_log(f"envoy cycling {route} {sim.envoy_cycling}", logit=True)
        sim.envoy_cycling -= 1
        update_index()
        abort(503, description=f"Envoy cycling {sim.envoy_cycling + 1}")

    # simulate timeout by delaying abort for 150 sec for any request
    request_ip = request.environ.get("REMOTE_ADDR")
    if sim.timeoutsim and request.path not in ("/info", "/info.xml", "/auth/check_jwt"):
        emit_log(f"Sleeping on {request_ip} {endpoint}", logit=True)
        sim.sleepers += 1
        update_index()
        await asyncio.sleep(sim.ip_sleep_time)
        if sim.sleepers > 0:
            sim.sleepers += -1
            update_index()
        abort(500, description=f"Envoy forced timeout {sim.ip_sleep_time}")

    # if next request should get override status apply it and reset
    if (sim.next_request_status) != 0:
        result = abs(sim.next_request_status)
        if sim.next_request_status > 0:
            sim.next_request_status = 0
        update_index()
        abort(result, "status overridden")


def update_cache_list(cachename: str = ""):
    """Send updates from cache."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        return
    list: str = "<ul>"
    list += "".join(
        [
            f'<li><a href="javascript:void(0);" id="{file}">{file}</a></li>'
            for file in sim.fixture_cache
        ]
    )
    list += "</ul>"
    emit("updateElement", {"cachefiles": f" {list}"}, broadcast=True, namespace="/")
    emit("showcachefile", {"data": cachename}, broadcast=True, namespace="/")
    # emit("updateElement", {"cachename": cachename}, broadcast=True, namespace="/")
    if sim.verbosity > 1:
        emit_log("updating cache list", logit=True)


def update_fixture_list(fixturename: str = ""):
    """Send updates from fixtures."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        return
    try:
        files: list[str] = [f.name for f in os.scandir(sim.fixture_folder())]
    except FileNotFoundError:
        files = []
    # if files == []:
    #     return
    files.sort()
    list: str = "<ul>"
    list += "".join(
        [
            f'<li><a href="javascript:void(0);" id="{file}">{file}</a></li>'
            for file in files
        ]
    )
    list += "</ul>"
    emit("updateElement", {"fixturefiles": f"{list}"}, broadcast=True, namespace="/")
    emit("showfixturefile", {"data": fixturename}, broadcast=True, namespace="/")
    # emit("updateElement", {"fixturename": ""}, broadcast=True, namespace="/")
    if sim.verbosity > 1:
        emit_log(f"updating fixture list {sim.fixture_folder()}", logit=True)
