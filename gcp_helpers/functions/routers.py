import json
import traceback
from collections import defaultdict
from functools import wraps
from typing import Callable

from flask import Request, make_response, Response


class HttpRouter:
    def __init__(self, prefix=''):
        self.__route_prefix = self._strip_path(prefix)
        self._routes = defaultdict(dict)

    @staticmethod
    def _error_handling_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(traceback.format_exc())
                # Handle the error and return an appropriate response
                error_message = f"An error occurred: {str(e)}"
                return make_response(error_message, 500)

        return wrapper

    def route(self, path: str, method: str = 'GET', error_handling: bool = True) -> Callable:
        def decorator(func: Callable) -> Callable:
            formatted_path = self._format_path(path)
            if error_handling:
                func = self._error_handling_decorator(func)
            self.register(func, formatted_path, method)
            return func

        return decorator

    @staticmethod
    def _strip_path(path: str):
        return path.strip().strip('/').strip()

    def _format_path(self, path: str):
        if self.__route_prefix != '':
            return f'/{self.__route_prefix}/{self._strip_path(path)}'
        else:
            return f'/{self._strip_path(path)}'

    def register(self, handler: Callable[[Request], Response], path: str, method: str = 'GET'):
        self._routes[method][path] = handler

    def _list_routes(self):
        print(json.dumps(self._routes, indent=2, default=str))

    def response(self, request: Request) -> Response:
        if request.method not in self._routes:
            return make_response("Method not allowed", 405)

        if request.path not in self._routes[request.method]:
            return make_response("Not found", 404)

        return self._routes[request.method][request.path](request)
