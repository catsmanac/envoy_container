"""envoy GET for json files."""

import copy
import logging
import random
from typing import Any

from awesomeversion import AwesomeVersion
from flask import abort, jsonify, request

from io_blueprint import IOBlueprint
from models.envoy_model import EnvoySim
from utils import (
    before_requests,
    emit_log,
    full_path,
    getsim,
    route_to_file,
    update_cache_list,
)

logger = logging.getLogger(__name__)
api_jsonget = IOBlueprint("api_jsonget", __name__)


@api_jsonget.before_request
async def before_request():
    """Process before request."""
    await before_requests()


def json_request():
    """Return json data from fixture file."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")
    content, status, file_loaded, added = sim.load_json(froute := route_to_file())
    if added:
        update_cache_list()

    # for inverters endpoint send empty list if overridden and count down
    if (froute) == "api_v1_production_inverters" and sim.empty_inverter_array:
        content = {}
        status = 200

    # for inverters endpoint force invalid json if overridden and count down
    elif froute == "api_v1_production_inverters" and sim.invalid_json:
        content = "invalid json"
        status = 200

    # if v1 production endpoint and envoy restart is active
    # send zero values for fw 3 until restart is complete
    elif (
        froute == "api_v1_production"
        and (sim.envoy_cycling > 0)
        and AwesomeVersion(sim.firmware).major == "3"
    ):
        sim.envoy_cycling -= 1
        segment: dict[str, int] = {}
        segment["wattHoursToday"] = 0
        segment["wattHoursSevenDays"] = 0
        segment["wattHoursLifetime"] = 0
        segment["wattsNow"] = 0
        content = segment
        status = 200

    # for tariff endpoint send 401, 404 or 503 status if overridden
    elif froute == "admin_lib_tariff" and ((_s := sim.next_tariff_status) > 0):
        content = (
            "Unauthorized"
            if _s == 401
            else "NotFound"
            if _s == 404
            else "Service Unavailable"
        )
        status = _s

    # for ACB finalize sleep state change one by one to sim delay
    elif froute == "inventory.json_deleted_1":
        found = False
        for inv in sim.fixture_cache[froute]:
            if inv["type"] == "ACB":
                for acb in inv["devices"]:
                    if acb["sleep_enabled"] and (
                        "envoy.cond_flags.pcu_ctrl.sleep-mode"
                        not in acb["device_status"]
                    ):
                        acb["device_status"].append(
                            "envoy.cond_flags.pcu_ctrl.sleep-mode"
                        )
                        found = True
                        break
                if found:
                    break

                for acb in inv["devices"]:
                    if (
                        not acb["sleep_enabled"]
                        and "envoy.cond_flags.pcu_ctrl.sleep-mode"
                        in acb["device_status"]
                    ):
                        acb["device_status"] = [
                            x
                            for x in acb["device_status"]
                            if x != "envoy.cond_flags.pcu_ctrl.sleep-mode"
                        ]
                        found = True
                        break
                if found:
                    break

    # for ivp/sc/sched send status 0 if sim is enabled
    elif froute == "ivp_sc_sched" and sim.sc_sched_status_0:
        content = {}
        status = 0

    # for /production set activeCount of production eim 0 if sim is enabled
    # and apply varying power if sim is enabled
    elif froute in ("production", "production.json", "production.json_details_1"):
        orig_content, status, file_loaded, added = sim.load_json(froute)
        content: dict[str, Any] = copy.deepcopy(orig_content)

        if sim.variable_power:
            factor = 0.5 + random.random()
            content["production"][1]["wNow"] *= factor
            for line in content["production"][1]["lines"]:
                line["wNow"] *= factor

        if sim.active_eim_0:
            content["production"][1]["activeCount"] = 0

    # for /ivp/meters/readings set ph1 data to 0 and agg value to ph2 if sim is enabled
    # and apply varying power if sim is enabled
    elif froute == "ivp_meters_readings":
        orig_content, status, file_loaded, added = sim.load_json(froute)
        content: dict[str, Any] = copy.deepcopy(orig_content)

        if sim.variable_power:
            factor = 0.5 + random.random()
            for meter in content:
                meter["activePower"] *= factor
                for channel in meter["channels"]:
                    channel["activePower"] *= factor

        if sim.store_ct_ph_1_0 and len(content) > 2 and len(content[2]["channels"]) > 1:
            for item, value in content[2]["channels"][1].items():
                if item not in ("eid", "timestamp"):
                    content[2]["channels"][0][item] = 0
                    content[2][item] = value

    emit_log(
        f'<code class="highlight">{request.method} {status} {full_path()}</code> '
        + f"fixture {file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status


@api_jsonget.route("/<path>", methods=["GET"])
def json_path_get(path: str):
    # https://python-markdown.github.io/extensions/
    """Return json data."""
    return json_request()


@api_jsonget.route("/<path:subpath>", methods=["GET"])
def json_subpath_get(subpath: str):
    # https://python-markdown.github.io/extensions/
    """Return json data."""
    return json_request()
