from functools import wraps

from flask import request

from ..service import vk_api_service


def require_access_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'error': 'Missing or invalid Authorization header'}, 401

        token = auth_header.split(' ')[1]

        try:
            user_id = vk_api_service.get_user_id(token)
        except Exception as e:
            return {'error': f'{e}'}, 400

        if not user_id:
            return {'error': 'Invalid or expired token'}, 401

        kwargs['user_id'] = user_id
        return func(*args, **kwargs)

    return wrapper
