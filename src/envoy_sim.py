"""Create flask application that simulates Envoy data from fixture files."""

from flask import Flask, Response, request
from flask_socketio import SocketIO
from flask_sslify import SSLify  # type: ignore

import blueprints
from app_setup import app_setup
from utils import emit_log, full_path

app = Flask(__name__)
app.config.update(app_setup())  # type: ignore
SSLify(app)  # redirect http to https

# use socketio for messages between server and client side
socketio = SocketIO(
    app,
    async_mode=app.config["async"],  # type: ignore
    logger=app.logger if (dev := app.config["dev"]) else False,  # type: ignore
    engineio_logger=app.logger if dev else False,
)
app.config["socketio"] = socketio

# All simulated endpoints are in blueprints
app.register_blueprint(blueprints.auth)
app.register_blueprint(blueprints.events)
app.register_blueprint(blueprints.api_jsonget)
app.register_blueprint(blueprints.api_jsonpost)
app.register_blueprint(blueprints.user)
app.register_blueprint(blueprints.api_xmlget)

app.app_context().push()


@app.after_request
def after_request(response: Response):
    """Handle after request for all paths."""
    # report error codes to interactive logger
    endpoint = full_path()
    if response.status_code >= 300:
        emit_log(
            '<code class="highlight">'
            + f"{request.method} {response.status} {endpoint}"
            + "</code>"
        )
    return response


if __name__ == "__main__":
    app.logger.info("starting socketio")

    # https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    ssl_mode = (  # type: ignore
        "adhoc"
        if app.config["cert"] == "adhoc"
        else (app.config["cert"], app.config["key"])
    )
    socketio.run(  # type: ignore
        app,
        host=app.config["host"],  # type: ignore
        port=app.config["port"],  # type: ignore
        ssl_context=ssl_mode,
        allow_unsafe_werkzeug=True,
    )
