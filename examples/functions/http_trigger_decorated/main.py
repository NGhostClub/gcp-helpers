from flask import Response, make_response

from gcp_helpers.functions.routers import HttpRouter

router = HttpRouter()


@router.route("/hello", "GET")
def hello_route(request) -> Response:
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        msg = request.args.get('message')
    elif request_json and 'message' in request_json:
        msg = request_json['message']
    else:
        msg = f'Hello World!'
    return make_response(msg, 200)


@router.route('/bye')
def bye_route(request) -> Response:
    return make_response("Bye Bye", 200)


def hello_world(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """

    return router.response(request)
