"""A Flask Blueprint class to be used with Flask-SocketIO.

This class inherits from the Flask Blueprint class so that
 we can use the standard Blueprint interface.

Derived from https://github.com/m-housh/io-blueprint
Original work by Michael Housh, mhoush@houshhomeenergy.com
Modified by Brian Wojtczak

@author Brian Wojtczak

See: https://gist.github.com/astrolox/445e84068d12ed9fa28f277241edf57b

Copyright 2020 Brian Wojtczak

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

# noinspection PyPackageRequirements
import socketio  # type: ignore
from flask import Blueprint


class IOBlueprint(Blueprint):
    """A Flask Blueprint class to be used with Flask-SocketIO."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace = self.url_prefix or "/"
        self._socketio_handlers = []
        self.socketio = None
        self.record_once(self.init_socketio)

    def init_socketio(self, state):
        self.socketio: socketio.Client = state.app.extensions["socketio"]
        for f in self._socketio_handlers:
            f(self.socketio)

        return self.socketio

    def on(self, key):
        """A decorator to add a handler to a blueprint."""

        def wrapper(f):
            def wrap(sio):
                @sio.on(key, namespace=self.namespace)
                def wrapped(*args, **kwargs):
                    return f(*args, **kwargs)

                return sio

            self._socketio_handlers.append(wrap)

        return wrapper

    def emit(self, *args, **kwargs):
        self.socketio.emit(*args, **kwargs)
