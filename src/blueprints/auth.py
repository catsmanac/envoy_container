"""Route for jwt checking."""

import logging
from datetime import datetime as dt
from typing import Any

import jwt
from flask import abort, make_response, redirect, request, url_for
from flask_socketio import emit  # type: ignore

from io_blueprint import IOBlueprint
from models.envoy_model import EnvoySim
from utils import before_requests, emit_log, getsim, update_index

logger = logging.getLogger(__name__)
auth = IOBlueprint("auth", __name__)


@auth.before_request
async def before_request():
    """Use common before request function."""
    await before_requests()


@auth.route("/auth/check_jwt", methods=["GET", "POST"])
def auth_check_jwt():
    """Mock Envoy token authentication."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")

    bearer = request.headers.get("Authorization")
    if not bearer or "Bearer" not in bearer:
        abort(401)

    token = bearer.split()[1]
    decoded = jwt.decode(token, options={"verify_signature": False})
    exp = dt.fromtimestamp(int(decoded["exp"])).strftime("%Y-%m-%d %H:%M:%S")
    emit_log(
        f"Token for {decoded.get('aud')} {decoded.get('username')} from "
        + f"{decoded.get('iss')} {decoded.get('enphaseUser')} {exp}"
    )

    sim.auth_count += 1
    emit(
        "authorized",
        {"data": f" {sim.authorized()} ({sim.auth_count})"},
        broadcast=True,
        namespace="/",
    )
    response = make_response("<!DOCTYPE html><h2>Valid token.</h2>")
    response.set_cookie("user_visit", str(1))
    emit_log(
        f'<code class="highlight">{request.path} {response.status}</code> '
        + f"{response.get_data() if sim.verbosity > 0 else ''}"
    )
    return response


@auth.route("/authorize", methods=["POST"])
def unauthorize():
    """Mark sim as (un)authorized to clear or force 401."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")
    sim.auth_count = 1 if sim.auth_count <= 0 else 0
    return redirect(url_for("user.index"))


@auth.on("btnauthorize")  # type: ignore
def btnauthorize(message: Any):
    """Process authorize button."""
    sim: EnvoySim | None = getsim()
    if not sim:
        return
    sim.auth_count = 1 if sim.auth_count <= 0 else 0
    logger.info(f"Toggled Auth to {sim.auth_count}")
    update_index()
    if sim.verbosity > 1:
        emit_log(f"Authorized {sim.authorized()} ({sim.auth_count})")
