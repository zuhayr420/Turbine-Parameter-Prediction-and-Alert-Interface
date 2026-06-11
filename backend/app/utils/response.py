from flask import jsonify

def success_response(data=None, message=None, status_code=200):
    payload = {'success': True}
    if message:
        payload['message'] = message
    if data is not None:
        if isinstance(data, dict):
            payload.update(data)
        else:
            payload['data'] = data
    return jsonify(payload), status_code

def error_response(code, message, status_code=400, details=None):
    payload = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }
    if details:
        payload['error']['details'] = details
    return jsonify(payload), status_code
