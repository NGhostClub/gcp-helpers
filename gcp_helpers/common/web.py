from flask import jsonify


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