import http.client
import json
import logging
from json import JSONDecodeError
import tornado.web
import tornado.websocket
import api


class Controller(tornado.web.RequestHandler):
    """
    Controller

    Attributes:
        app (Result): The app instance
        json_args (Dict): JSON Data
    """

    route = None

    def __init__(self, application, request, **kwargs):
        self.app = api.API.app
        self.json_args = None
        super().__init__(application, request, **kwargs)

    def prepare(self):
        headers = self.request.headers
        self.json_args = {}
        if "Content-Type" in headers and headers["Content-Type"].startswith("application/json"):
            try:
                body = self.request.body
                if isinstance(body, bytes):
                    body = body.decode()
                self.json_args = json.loads(body)
            except JSONDecodeError as e:
                logging.warning(e.msg)
                raise tornado.web.HTTPError(400, reason="Could not parse JSON data.")

    def write_error(self, status_code, **kwargs):
        info = kwargs.get("exc_info")
        try:
            if info is not None and len(info) > 2 and hasattr(info[1], "reason") and info[1].reason is not None:
                self.write({"message": info[1].reason})
            else:
                self.write({"message": http.client.responses[status_code]})
        except TypeError:
            self.write({"message": http.client.responses[status_code]})

    def write(self, chunk, set_content_type=True, status_code=None):
        if status_code is not None:
            self.set_status(status_code)
        if chunk is None:
            return
        if isinstance(chunk, (dict, list)):
            chunk = json.dumps(chunk)
        if set_content_type:
            self.set_header('Content-Type', 'application/json')
        super().write(chunk)


class WebSocketController(tornado.websocket.WebSocketHandler):
    """
    SwimSuite Controller

    Attributes:
        app (Result): The app instance
    """

    route = None

    def __init__(self, application, request, **kwargs):
        self.app = api.API.app
        super().__init__(application, request, **kwargs)

    def check_origin(self, origin):
        if __debug__:
            return True
        return super().check_origin(origin)

    def write_message(self, message, binary=False):
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        super().write_message(message, binary)
