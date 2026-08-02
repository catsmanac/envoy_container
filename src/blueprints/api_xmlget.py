"""envoy GET for xml files."""

import logging

from flask import Response, abort, request

from io_blueprint import IOBlueprint
from models.envoy_model import EnvoySim
from utils import before_requests, emit_log, getsim, route_to_file

logger = logging.getLogger(__name__)
api_xmlget = IOBlueprint("api_xmlget", __name__)


@api_xmlget.before_request
async def before_request():
    """Procces before reqest."""
    await before_requests()


@api_xmlget.route("/info", methods=["GET"])
@api_xmlget.route("/info.xml", methods=["GET"])
def info():
    """Return xml data."""
    sim: EnvoySim | None = getsim()
    if sim is None:
        logger.info("service unavailable")
        abort(503, "No sim loaded")
    content, status, file_loaded, added = sim.load_text_file(route_to_file())
    emit_log(
        f'<code class="highlight">{request.method} {status} {request.path}</code> '
        + f"{file_loaded} {content if sim.verbosity > 0 else ''}"
    )
    return Response(content, mimetype="text/xml"), status
