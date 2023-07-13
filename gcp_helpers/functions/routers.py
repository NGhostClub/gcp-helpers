import json
import traceback
from collections import defaultdict
from functools import wraps
from typing import Callable

from flask import Request, make_response, Response

from gcp_helpers.functions.decorators import default_error_handling


class Factory:
    def __init__(self):
        self.route_prefix = ""
        self.routes = defaultdict(dict)

    def set_prefix(self, prefix: str):
        self.route_prefix = self._strip_path(prefix)

    def route(self, path: str, method: str = 'GET', error_handling: bool = True) -> Callable:
        def decorator(func: Callable) -> Callable:
            formatted_path = self._format_path(path)
            if error_handling:
                func = default_error_handling(func)
            self.register(func, formatted_path, method)
            return func

        return decorator

    @staticmethod
    def _strip_path(path: str):
        return path.strip().strip('/').strip()

    def _format_path(self, path: str):
        if self.route_prefix != '':
            return f'/{self.route_prefix}/{self._strip_path(path)}'
        else:
            return f'/{self._strip_path(path)}'

    def register(self, handler: Callable[[Request], Response], path: str, method: str = 'GET'):
        self.routes[method][path] = handler

    def _list_routes(self):
        print(json.dumps(self.routes, indent=2, default=str))


class HttpRouter(Factory):

    def connect_factory(self, factory: Factory):
        prefix = self.route_prefix
        routes = self.routes

        if prefix:
            prefix = f"{prefix}"

        for method, route in factory.routes.items():
            for path, func in route.items():
                routes[method][f"{prefix}{path}"] = func

    def response(self, request: Request) -> Response:
        if request.method not in self.routes:
            return make_response("Method not allowed", 405)

        if request.path not in self.routes[request.method]:
            return make_response("Not found", 404)

        return self.routes[request.method][request.path](request)
