"""Routes for user facing part of the envoy simulator."""

import logging

import markdown
from flask import current_app, render_template, request, send_from_directory
from flask_socketio import SocketIO

from io_blueprint import IOBlueprint
from models.envoy_model import EnvoySim
from utils import getsim, sim_paths

logger = logging.getLogger(__name__)
user = IOBlueprint("user", __name__)


# default landing
@user.route("/", methods=["GET", "POST"])
def index():
    """Show main user page."""
    sim: EnvoySim | None = getsim()
    socketio: SocketIO = current_app.config.get("socketio")  # type: ignore
    return render_template(
        "index.html",
        sim=sim,
        sims=sim_paths(),  # list of found folders with fixture files
        async_mode=socketio.async_mode,  # type: ignore
    )  # type: ignore


# landing for readme.md converted to html
@user.route("/readme", methods=["GET"])
def readme():
    """Show readme user page, covert from md to html."""
    try:
        with open("./templates/README.md") as f:
            readmemd = f.read()
        # https://python-markdown.github.io/extensions/
        return markdown.markdown(
            readmemd, extensions=["toc", "fenced_code", "tables"]
        ), 200  # type: ignore
    except FileNotFoundError:
        return render_template("README.md not found")


@user.route("/favicon.ico")
def favicon():
    """Provide favicon.ico."""
    return send_from_directory(
        "./static", "flask-logo.ico", mimetype="image/vnd.microsoft.icon"
    )


@user.route("/flask-logo.png")
@user.route("/configuration.png")
@user.route("/log.png")
@user.route("/cache.png")
@user.route("/fixtures.png")
def logo():
    """Provide png files."""
    return send_from_directory(
        "./static", request.path[1:], mimetype="image/vnd.microsoft.icon"
    )
