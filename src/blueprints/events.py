"""Handle socketio events at the server side (in python)."""

import logging
from typing import Any

from flask import current_app, request
from flask_socketio import emit  # type: ignore

from io_blueprint import IOBlueprint
from models.envoy_model import EnvoySim
from utils import emit_log, getsim, update_cache_list, update_fixture_list, update_index

logger = logging.getLogger(__name__)
events = IOBlueprint("events", __name__)


@events.on("btnchangesim")  # type: ignore
def change_sim(message: Any):
    """Execute activate path button press."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    if not message.get("data"):
        return
    emit_log(f"Loading sim {(newpath := message['data'])}", logit=True)
    # update app config
    current_app.config["path"] = newpath
    # change path in current sim
    sim.path = newpath
    # update the list of fixture files
    update_fixture_list()
    # restart the sim using new path
    sim.start_sim()
    # refresh the cache list
    update_cache_list()
    # update index page fields
    update_index()


@events.on("btnverbosity")  # type: ignore
def btnverbosity(message: Any):
    """Toggle verbosity 0-1-2-0 on each verbosity button click."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    sim.verbosity += 1 if sim.verbosity < 2 else -2
    update_index()
    emit_log(f"Setting Verbosity to {sim.verbosity}", True)


@events.on("btnrestart")  # type: ignore
def btnrestart(message: Any):
    """Restart sim and set restarting counter or reset counter if active."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    # reset restart counter if already running
    if sim.envoy_cycling > 0:
        sim.envoy_cycling = 0
        update_index()
        return
    # restart the sim and simulate  some time needed
    sim.cycle_envoy()
    update_index()
    if sim.verbosity > 0:
        emit_log("Initiated envoy cycle", True)


def toggle_bool(attribute: Any):
    """Toggle value of boolean sim attribute."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    target = not getattr(sim, attribute)
    setattr(sim, attribute, target)
    update_index()
    if sim.verbosity > 1:
        emit_log(f"Setting {attribute} to {target}", True)


@events.on("btntimeoutsim")  # type: ignore
def btntimeoutsim(message: Any):
    """Toggle timeout simulation on/off each Timeout On button click."""
    toggle_bool("timeoutsim")


@events.on("btnemptyinverter")  # type: ignore
def btnemptyinverter(message: Any):
    """Toggle empy inverters array simulation on/off each button click."""
    toggle_bool("empty_inverter_array")


@events.on("btninvalidjson")  # type: ignore
def btninvalidjson(message: Any):
    """Toggle empy inverters array simulation on/off each button click."""
    toggle_bool("invalid_json")


@events.on("btncacherefresh")  # type: ignore
def btncacherefresh(message: Any):
    """Execute cache list refresh."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    update_cache_list()
    if sim.verbosity > 1:
        emit_log("cache list refresh", True)


@events.on("btnfixturefresh")  # type: ignore
def btnfixturefresh(message: Any):
    """Execute fixture list refresh."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    # update the fixture list
    update_fixture_list()
    if sim.verbosity > 1:
        emit_log("fixture list refresh", True)


def set_next_status(attribute: Any, value: int):
    """Set next status value to use."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    target = value
    setattr(sim, attribute, target)
    update_index()
    if sim.verbosity > 1:
        emit_log(f"Next status {attribute}: {target}", True)


@events.on("btn401")  # type: ignore
def btn401(message: Any):
    """Set next request status 401."""
    set_next_status("next_request_status", 401)


@events.on("btn404")  # type: ignore
def btn404(message: Any):
    """Set next request status 404."""
    set_next_status("next_request_status", 404)


@events.on("btn503")  # type: ignore
def btn503(message: Any):
    """Set next request status 503."""
    set_next_status("next_request_status", 503)


@events.on("btnstatusclear")  # type: ignore
def btnstatuclears(message: Any):
    """Set next request status default."""
    set_next_status("next_request_status", 0)


@events.on("btntariff401")  # type: ignore
def btntariff401(message: Any):
    """Set next tariff request status 401."""
    set_next_status("next_tariff_status", 401)


@events.on("btntariff404")  # type: ignore
def btntariff404(message: Any):
    """Set next tariff request status 404."""
    set_next_status("next_tariff_status", 404)


@events.on("btntariff503")  # type: ignore
def btntariff503(message: Any):
    """Set next tariff request status 503."""
    set_next_status("next_tariff_status", 503)


@events.on("btntariffstatusclear")  # type: ignore
def btntariffstatusclear(message: Any):
    """Set next tariff request status default."""
    set_next_status("next_tariff_status", 0)


@events.on("showfixturefile")  # type: ignore
def showfixturefile(message: Any):
    """Show fixture file content in viewer."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    target = message["data"]
    # update file name field
    emit("updateElement", {"fixturename": target}, broadcast=True, namespace="/")
    if "info" in target:
        # info is xml file
        j = sim.load_text_file(target, cache_it=False, from_cache=False)[0]
        emit("updateXML", {"fixture_viewer": j}, broadcast=True, namespace="/")
    else:
        # show json file content
        j = sim.load_json(target, cache_it=False, from_cache=False)[0]
        emit("updateJSON", {"fixture_viewer": j}, broadcast=True, namespace="/")


@events.on("showcachefile")  # type: ignore
def showcachefile(message: Any):
    """Show cache file content in viewer."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    target = message["data"]
    j = sim.fixture_cache[target]
    # update file name field
    emit("updateElement", {"cachename": target}, broadcast=True, namespace="/")
    if "info" in target:
        # info is xml file
        emit("updateXML", {"cache_viewer": j.decode()}, broadcast=True, namespace="/")
    else:
        # show json file content
        emit("updateJSON", {"cache_viewer": j}, broadcast=True, namespace="/")


@events.on("connect")  # type: ignore
def connect(message: Any):
    """Log connection made."""
    update_cache_list()
    update_fixture_list()
    # this creates the first entry in the log viewer.
    emit_log(f"{request.remote_addr} connected to {request.path}")
    update_index()
