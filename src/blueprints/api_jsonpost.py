"""envoy PUT/POST for json data."""

import json
import logging
from typing import Any

from flask import abort, jsonify, request

from io_blueprint import IOBlueprint
from models.envoy_model import EnvoySim
from utils import before_requests, emit_log, getsim, route_to_file, update_cache_list

logger = logging.getLogger(__name__)
api_jsonpost = IOBlueprint("api_jsonpost", __name__)


@api_jsonpost.before_request
async def before_request():
    """Process before request."""
    await before_requests()


def abort_on_bad_status(status: int, target_file: str, added: bool):
    """Abort if status >300 or update cache list."""
    if status >= 300:
        logger.info("file load failed")
        abort(status, f"Error loading {target_file}")
    if added:
        update_cache_list()


@api_jsonpost.route("/admin/lib/tariff", methods=["PUT", "POST"])
def post_tariff():
    """PUT, POST tariff data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    # for tariff endpoint send 401, 404 or 503 status if overridden
    if (_s := sim.next_tariff_status) > 0:
        content = (
            "Unauthorized"
            if _s == 401
            else "NotFound"
            if _s == 404
            else "Service Unavailable"
        )
        status = _s
        return jsonify(content), status

    # get posted data
    req_content: dict[str, Any] = json.loads(request.data)
    emit_log(
        f'<code class="highlight">{request.path} update</code> '
        + f"{req_content if sim.verbosity > 0 else ''}",
        True,
    )

    # make sure route data is in cache
    content, status, file_loaded, added = sim.load_json(route_to_file())
    abort_on_bad_status(status, file_loaded, added)

    # update tariff data in cache
    sim.fixture_cache[file_loaded] = {
        "tariff": req_content["tariff"],
        "schedule": sim.fixture_cache["admin_lib_tariff"]["schedule"],
    }
    content, status, file_loaded, added = sim.load_json(file_loaded)

    emit_log(
        f'<code class="highlight">{request.path} {status}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status


@api_jsonpost.route("/ivp/ensemble/relay", methods=["POST"])
def post_relay():
    """POST relay data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    # get posted data
    req_content: dict[str, Any] = json.loads(request.data)
    emit_log(
        f'<code class="highlight">{request.path} update</code> '
        + f"{req_content if sim.verbosity > 0 else ''}",
        True,
    )

    # make sure required data is in cache
    content, status, file_loaded, added = sim.load_json(route_to_file())
    abort_on_bad_status(status, file_loaded, added)

    # update relay data in cache
    for item in sim.fixture_cache[file_loaded]:
        if item["type"] == "ENPOWER":
            for k, v in req_content.items():
                item["devices"][0][k] = v
    content, status, file_loaded, added = sim.load_json(file_loaded)

    emit_log(
        f'<code class="highlight">{request.path} {status}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status


@api_jsonpost.route("/ivp/ensemble/dry_contacts", methods=["POST"])
def post_dry_contacts():
    """POST dry contact data data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    # get posted data
    req_content: dict[str, Any] = json.loads(request.data)
    emit_log(
        f'<code class="highlight">{request.path} update</code> '
        + f"{req_content if sim.verbosity > 0 else ''}",
        True,
    )

    # make sure route data is in cache
    content, status, file_loaded, added = sim.load_json(route_to_file())
    abort_on_bad_status(status, file_loaded, added)

    # update dry contact data in cache
    id = req_content["dry_contacts"]["id"]
    for idx, item in enumerate(
        contacts := sim.fixture_cache[content[2]]["dry_contacts"]
    ):
        if item["id"] == id:
            # print(item)
            # print(req_content["dry_contacts"])
            contacts[idx] = req_content["dry_contacts"]
            # print(item)
    content, status, file_loaded, added = sim.load_json(file_loaded)

    emit_log(
        f'<code class="highlight">{request.path} {status}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status


@api_jsonpost.route("/ivp/ss/dry_contact_settings", methods=["POST"])
def post_dry_contact_settings():
    """POST dry contact data data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    # get posted data
    req_content: dict[str, Any] = json.loads(request.data)
    emit_log(
        f'<code class="highlight">{request.path} update</code> '
        + f"{req_content if sim.verbosity > 0 else ''}",
        True,
    )

    # make sure route data is in cache
    content, status, file_loaded, added = sim.load_json(route_to_file())
    abort_on_bad_status(status, file_loaded, added)

    # update dry contact data in cache
    id = req_content["dry_contacts"]["id"]
    for item in sim.fixture_cache[content[2]]["dry_contacts"]:
        if item["id"] == id:
            item = req_content["dry_contacts"]
    content, status, file_loaded, added = sim.load_json(file_loaded)

    emit_log(
        f'<code class="highlight">{request.path} {status}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status


@api_jsonpost.route("/admin/lib/acb_config", methods=["PUT"])
@api_jsonpost.route("/admin/lib/acb_config.json", methods=["PUT"])
def json_post():
    """PUT json data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    # get posted data
    req_content: dict[str, Any] = json.loads(request.data)
    emit_log(
        f'<code class="highlight">{request.path} put</code> '
        + f"{req_content if sim.verbosity > 0 else ''}",
        True,
    )

    # make sure route data is in cache
    content, status, file_loaded, added = sim.load_json(route_to_file())
    abort_on_bad_status(status, file_loaded, added)

    req_sleep = req_content["acb_sleep"]
    for sleep in req_sleep:
        found: bool = False
        for item in sim.fixture_cache[content[2]]["acb_sleep"].values():
            if item["serial_num"] == sleep["serial_num"]:
                item["sleep_min_soc"] = sleep["sleep_min_soc"]
                item["sleep_max_soc"] = sleep["sleep_max_soc"]
                found = True
        if not found:
            sim.fixture_cache[content[2]]["acb_sleep"].append(sleep)
    content, status, file_loaded, added = sim.load_json(file_loaded)

    emit_log(
        f'<code class="highlight">{request.path} {status}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status


@api_jsonpost.route("/admin/lib/acb_config", methods=["DELETE"])
@api_jsonpost.route("/admin/lib/acb_config.json", methods=["DELETE"])
def json_delete():
    """DEKLETE json data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    # get posted data
    req_content: dict[str, Any] = json.loads(request.data)
    emit_log(
        f'<code class="highlight">{request.path} delete</code> '
        + f"{req_content if sim.verbosity > 0 else ''}",
        True,
    )

    # make sure route data is in cache
    content, status, file_loaded, added = sim.load_json(route_to_file())
    abort_on_bad_status(status, file_loaded, added)

    if "acb_sleep" in sim.fixture_cache[content[2]]:
        acb_sleep = req_content["acb_sleep"]
        for sleep in acb_sleep:
            for item in sim.fixture_cache[content[2]]["acb_sleep"].values():
                if item["serial_num"] == sleep["serial_num"]:
                    item["sleep_min_soc"] = None
                    item["sleep_max_soc"] = None
    content, status, file_loaded = {"message": "success"}, 200, file_loaded

    emit_log(
        f'<code class="highlight">{request.path} {status}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}",
        True,
    )
    return jsonify(content), status
