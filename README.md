# Overview
**gcp-ng-helpers** is a Python library that provides helper functions for 
interacting with Google Cloud Platform (GCP) services.

# Installation

Use the package manager pip to install gcp-ng-helpers

```commandline
pip install gcp-ng-helpers
```

# Functions submodule
## Http Router
Cloud function by default only serves single '/' (root) http endpoint.
With this Http Router you can easy serve much more, without need to parse 
Request object for method and path
### Usage
Define a function with flask.Request argument
returning the flaks.Response object
Import HttpRouter from functions submodule and register defined function
as route with path and method
Then inside cloud function entry point function return router.response

```python
from flask import Request, Response, make_response
from gcp_helpers.functions.routers import HttpRouter


def hello_route(request: Request) -> Response:
    return make_response('Hello', 200)


router = HttpRouter()
router.register(hello_route, '/hello', 'GET')

def main(request):
    return router.response(request)
```