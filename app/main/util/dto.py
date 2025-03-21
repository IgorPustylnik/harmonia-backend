import os
from datetime import datetime
from flask_restx import Namespace, fields

host_url = os.getenv('HOST_URL')


class ArrangementDTO:
    api = Namespace('arrangements', description='Arrangements related operations')

    create_arrangement = api.model('Create arrangement', {
        'name': fields.String(required=True, description='Name of the arrangement', example='Cool music'),
        'bpm': fields.Integer(required=True, description='BPM', example=120),
        'tags': fields.String(description='Tags for desired melody', example='rock, energetic'),
    })

    rename_arrangement = api.model('Rename arrangement', {
        'name': fields.String(required=True, description='Name of the arrangement', example='Cool music')
    })

    create_arrangement_response = api.model('Create arrangement response', {
        'status': fields.String(description='Status of the arrangement', example='success'),
        'message': fields.String(description='Message', example='Arrangement added successfully'),
        'id': fields.Integer(description='Arrangement ID', example=1)
    })

    arrangement = api.model('Arrangement', {
        'id': fields.Integer(description='Arrangement ID', example=1),
        'name': fields.String(description='Arrangement name', example='My Awesome Arrangement'),
        'bpm': fields.Integer(description='Beats per minute', example=160),
        'tags': fields.String(description='Arrangement tags', example='rock, energetic'),
        'file': fields.String(description='Arrangement file', example=f'{host_url}/api/arrangements/file/1'),
        'created_at': fields.DateTime(description='Arrangement created at', example=str(datetime.utcnow())),
        'status': fields.String(description='Status of the arrangement', example='PENDING'),
    })

    arrangements_list = api.model('Arrangements paged list with search query', {
        'count': fields.Integer(description='Number of arrangements on the page', example=24),
        'pages': fields.Integer(description='Total number of pages', example=3),
        'next': fields.String(description='Next page', example=f'{host_url}/api/arrangements/?page=2&search_query=awesome'),
        'prev': fields.String(description='Previous page', example="null"),
        'results': fields.List(fields.Nested(arrangement), description='List of arrangements')
    })

    upload_video = api.model('Upload video', {
        'url': fields.String(description='Link for video to be uploaded to', example='https://ovu.mycdn.me/upload.do?sig=6c...')
    })


class UserDTO:
    api = Namespace('user', description='User related operations')
