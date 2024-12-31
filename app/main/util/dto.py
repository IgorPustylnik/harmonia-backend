from datetime import datetime

from flask_restx import Namespace, fields


class ArrangementDTO:
    api = Namespace('arrangements', description='Arrangements related operations')

    create_arrangement = api.model('Create arrangement', {
        'name': fields.String(required=True, description='Name of the arrangement', example='Cool music'),
        'bpm': fields.Integer(required=True, description='BPM', example=120),
        'tags': fields.String(description='Tags for desired melody', example='rock, energetic'),
    })

    create_arrangement_response = api.model('Create arrangement response', {
        'status': fields.String(description='Status of the arrangement', example='success'),
        'message': fields.String(description='Message', example='Arrangement added successfully'),
        'id': fields.Integer(description='Arrangement ID', example=1)
    })

    get_arrangement_file = api.model('Get arrangement file', {
        'id': fields.Integer(required=True, description='Arrangement ID', example=1)
    })

    arrangement = api.model('Arrangement', {
        'id': fields.Integer(description='Arrangement ID', example=1),
        'name': fields.String(description='Arrangement name', example='My Awesome Arrangement'),
        'bpm': fields.Integer(description='Beats per minute', example=160),
        'tags': fields.String(description='Arrangement tags', example='rock, energetic'),
        'created_at': fields.DateTime(description='Arrangement created at', example=str(datetime.utcnow())),
        'status': fields.String(description='Status of the arrangement', example='PENDING'),
    })

    arrangements_list = api.model('ArrangementsList', {
        'arrangements': fields.List(fields.Nested(arrangement), description='List of arrangements')
    })

    vk_id = api.model('VK ID', {
        'user_id': fields.Integer(required=True, description='VK user ID', example=1),
    })


class RegisterDTO:
    api = Namespace('auth', description='Authentication related operations')
    vk_id = api.model('VK ID', {
        'user_id': fields.Integer(required=True, description='User\'s VK ID', example=1)
    })
