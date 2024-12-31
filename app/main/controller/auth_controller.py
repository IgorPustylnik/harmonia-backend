from flask_restx import Resource

from ..util.dto import RegisterDTO

api = RegisterDTO().api
vk_id = RegisterDTO().vk_id


@api.route('/register')
class Create(Resource):
    @api.doc(description='Register a user')
    @api.expect(vk_id)
    @api.response(201, 'Registered a user')
    def post(self):
        return {'message': "Registered a user"}, 201
