from flask_restx import Resource
from flask import request
from ..util.dto import UserDTO
from ..service.database import user_service
from ..controller import extract_user_id

api = UserDTO().api


@api.route('/register')
class Register(Resource):
    @api.doc(description='Register a user', security='access_token')
    @api.response(201, 'Registered a user')
    def post(self):
        user_id = extract_user_id(request)
        if user_id is None:
            return {'error': 'Missing or invalid Authorization header'}, 401

        return user_service.register_user(user_id)
