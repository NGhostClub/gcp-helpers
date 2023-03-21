from gcp_helpers.functions.routers import HttpRouter


def hello_world(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    router = HttpRouter()
    router.register(hello_route, '/hello', 'GET')
    router.register(bye_route, '/bye', 'GET')

    return router.response(request)


def hello_route(request):
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        return request.args.get('message')
    elif request_json and 'message' in request_json:
        return request_json['message']
    else:
        return f'Hello World!'


def bye_route(request):
    return f'Bye Bye World!'
