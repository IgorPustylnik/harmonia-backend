import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from flask import request, send_file, abort
from flask_restx import Resource

from .. import s3_storage
from ..util import converter
from ..util.decorator import require_access_token
from ..util.dto import ArrangementDTO
from ..service.database import arrangement_service, user_service
from ..controller import websocket_controller

api = ArrangementDTO().api
create_arrangement = ArrangementDTO().create_arrangement
create_arrangement_response = ArrangementDTO().create_arrangement_response
single_arrangement = ArrangementDTO().arrangement
arrangements_list = ArrangementDTO().arrangements_list

executor = ThreadPoolExecutor(max_workers=5)


@api.route('/create')
class CreateArrangement(Resource):
    @api.doc(description='Create an arrangement', security='access_token')
    @api.expect(create_arrangement)
    @api.response(201, 'Success', model=create_arrangement_response)
    @require_access_token
    def post(self, user_id):
        if 'file' not in request.files:
            return {'error': 'No file part in the request'}, 400

        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400

        json_string = request.form.get('json')

        if not json_string:
            return {'error': 'No JSON data provided'}, 400

        data = json.loads(json_string)
        data["user_id"] = user_id

        result = arrangement_service.add_arrangement(data)

        if result[1] == 201:
            arrangement_id = int(result[0]['id'])
            drums_file = bytes(file.read())
            executor.submit(arrangement_service.generate_music,
                            arrangement_id=arrangement_id,
                            drums_file=drums_file,
                            bpm=data['bpm'],
                            tags=data['tags'],
                            completion=websocket_controller.data_updated(user_id))

        return result


@api.route('/')
class ArrangementsList(Resource):
    @api.doc(description='Get an arrangements list', security='access_token',
             params={'page': {'description': 'Number of page', 'type': 'integer'},
                     'filter': {'description': 'Filter query', 'type': 'string'}})
    @api.response(200, 'Success', model=arrangements_list)
    @require_access_token
    def get(self, user_id):
        page = request.args.get('page', 1, type=int)
        filter_query = request.args.get('filter', '', type=str)
        try:
            try:
                if user_service.get_user(user_id) is None:
                    return {'error': 'User does not exist'}, 400
            except Exception as e:
                return {'error': str(e)}, 400

            arrangements = arrangement_service.get_user_arrangements(user_id, page, filter_query)
            return arrangements
        except Exception as e:
            return {'error': str(e)}, 400


@api.route('/<int:arrangement_id>')
class SingleArrangement(Resource):
    @api.doc(description='Get a single arrangement', security='access_token')
    @api.response(200, 'Success', model=single_arrangement)
    @require_access_token
    def get(self, user_id, arrangement_id):
        try:
            arrangement = arrangement_service.get_arrangement(arrangement_id)

            if arrangement and arrangement.user_id == user_id:
                return converter.arrangement_to_dict(arrangement), 200
            elif arrangement:
                return {'error': 'Access denied'}, 403

            return {'error': 'Arrangement not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


@api.route('/file/<int:arrangement_id>')
class ArrangementFile(Resource):
    @api.doc(description='Get an arrangement file', produces=['application/octet-stream'], security='access_token')
    @api.response(200, 'File received')
    @require_access_token
    def get(self, user_id, arrangement_id):
        arrangement = arrangement_service.get_arrangement(arrangement_id)

        if not arrangement:
            return {'error': 'Arrangement not found'}, 404
        elif arrangement.user_id != user_id:
            return {'error': 'Access denied'}, 403

        file_name = arrangement.file_name
        arrangement_name = arrangement.name

        if not file_name:
            return {"message": "File not found."}, 404

        try:
            file_data = s3_storage.get(file_name)

            if not file_data:
                return {"message": "File content is empty or not found."}, 404

            byte_io = BytesIO(file_data)
            byte_io.seek(0)

            return send_file(
                byte_io,
                as_attachment=True,
                download_name=arrangement_name,
                mimetype='application/octet-stream'
            )
        except Exception as e:
            abort(500, "Error sending file.")
