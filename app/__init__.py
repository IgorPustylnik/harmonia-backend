from flask_restx import Api
from flask import Blueprint

from .main.controller.arrangements_controller import api as arrangements_ns
from .main.controller.auth_controller import api as auth_ns

blueprint = Blueprint('api', __name__, url_prefix="/api")
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
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
api.add_namespace(auth_ns)
