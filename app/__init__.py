from flask_restx import Api
from flask import Blueprint

from .main.controller.arrangements_controller import api as arrangements_ns
from .main.controller.user_controller import api as user_ns

blueprint = Blueprint('api', __name__, url_prefix="/api")
authorizations = {
    'access_token': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Add 'Bearer <your_token>'"
    }
}

api = Api(
    blueprint,
    title='Harmonia API',
    version='0.1',
    description='AI Music creation tool',
    authorizations=authorizations,
    security='apikey'
)

api.add_namespace(arrangements_ns)
api.add_namespace(user_ns)
