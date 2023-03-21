import base64
from functools import wraps
from flask import Request, make_response


class MissingPositionalArgumentError(Exception):
    def __init__(self, message="At least one positional argument must be defined"):
        super().__init__(message)


class NotFlaskRequestError(Exception):
    def __init__(self, ptype: type):
        super().__init__(f"Type mismatch")


class Guard:
    def __init__(self):
        self.basic_auth_token: str | None = None
        self.headers: dict[str, str] = {}
        self.basic_auth: bool = False
        self._accept_json = False

    def accept_json(self, value: bool):
        self._accept_json = value
        if value:
            self.add_header("Content-type", "application/json")
        else:
            self.headers.pop("Content-type")

    @staticmethod
    def _check_json(req: Request):
        if req is not None and not req.is_json:
            return False
        else:
            return True

    def guard_json(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            req = self._get_request(*args)

            if not self._check_json(req):
                return make_response("Bad request", 400)
            else:
                return func(*args, **kwargs)
        return wrapper

    def add_header(self, key: str, value: str):
        self.headers.update({key: value})

    def _check_headers(self, req: Request):
        missing = []
        for k, v in self.headers.items():
            if k not in req.headers.keys() or v != req.headers[k]:
                missing.append(k)
        if req is not None and len(missing) > 0:
            print("Missing headers:\n", "\n - ".join(missing))
            return False
        else:
            return True

    @staticmethod
    def _get_request(*args):
        try:
            req: Request = args[0]
        except IndexError:
            raise MissingPositionalArgumentError
        if not isinstance(req, Request):
            raise NotFlaskRequestError(type(req))
        return req

    def guard_headers(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            req = self._get_request(*args)

            if not self._check_headers(req):
                return make_response("Bad request. Headers is missing", 400)
            else:
                return func(*args, **kwargs)
        return wrapper

    def set_basic_auth(self, username, password):
        self.basic_auth = True
        self.basic_auth_token = base64.b64encode(
            bytes(f"{username}:{password}".encode('utf8'))).decode("utf8")
        self.headers.update({
                "Authorization": f"Basic {self.basic_auth_token}"
        })

    def _check_basic_auth(self, req: Request):
        if req.headers.get("Authorization", None) is None:
            return False
        if req is not None and req.headers.get("Authorization") != f"Basic {self.basic_auth_token}":
            return False
        return True

    def guard_basic_auth(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            req = self._get_request(*args)

            if not self._check_basic_auth(req):
                return make_response("Forbidden", 403)
            else:
                return func(*args, **kwargs)
        return wrapper

    def guard(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            req = self._get_request(*args)
            if self.basic_auth and not self._check_basic_auth(req):
                return make_response("Forbidden", 403)
            if not self._check_headers(req):
                return make_response("Bad request", 400)
            if self._accept_json and not self.guard_json(req):
                return make_response("Bad request", 400)
            return func(*args, **kwargs)
        return wrapper

