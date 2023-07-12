import json
import traceback
from collections import defaultdict
from functools import wraps
from typing import Callable

from flask import Request, make_response, Response, jsonify


class CustomResponse:
    @staticmethod
    def success(data=None, message=None):
        response = {
            'success': True,
            'data': data,
            'message': message
        }
        return jsonify(response), 200

    @staticmethod
    def bad_request(message=None):
        response = {
            'success': False,
            'message': message or 'Bad request'
        }
        return jsonify(response), 400

    @staticmethod
    def unauthorized(message=None):
        response = {
            'success': False,
            'message': message or 'Unauthorized'
        }
        return jsonify(response), 401

    @staticmethod
    def forbidden(message=None):
        response = {
            'success': False,
            'message': message or 'Forbidden'
        }
        return jsonify(response), 403

    @staticmethod
    def not_found(message=None):
        response = {
            'success': False,
            'message': message or 'Not found'
        }
        return jsonify(response), 404

    @staticmethod
    def server_error(message=None):
        response = {
            'success': False,
            'message': message or 'Internal server error'
        }
        return jsonify(response), 500


class Factory:
    def __init__(self):
        self.route_prefix = ""
        self.routes = defaultdict(dict)

    def set_prefix(self, prefix: str):
        self.route_prefix = self._strip_path(prefix)

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
