import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from flask import request, send_file, abort
from flask_restx import Resource

from .. import s3_storage
from ..util.dto import ArrangementDTO
from app.main.service.database import arrangement_service, user_service

api = ArrangementDTO().api
create_arrangement = ArrangementDTO().create_arrangement
create_arrangement_response = ArrangementDTO().create_arrangement_response
single_arrangement = ArrangementDTO().arrangement
arrangements_list = ArrangementDTO().arrangements_list
vk_id = ArrangementDTO().vk_id

executor = ThreadPoolExecutor(max_workers=5)


@api.route('/create')
class CreateArrangement(Resource):
    @api.doc(description='Create an arrangement')
    @api.expect(create_arrangement)
    @api.response(201, 'Success', model=create_arrangement_response)
    def post(self):
        if 'file' not in request.files:
            return {'error': 'No file part in the request'}, 400

        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400

        json_string = request.form.get('json')

        if not json_string:
            return {'error': 'No JSON data provided'}, 400

        data = json.loads(json_string)

        result = arrangement_service.add_arrangement(data)

        if result[1] == 201:
            arrangement_id = int(result[0]['id'])
            drums_file = bytes(file.read())
            executor.submit(arrangement_service.generate_music,
                            arrangement_id=arrangement_id,
                            drums_file=drums_file,
                            bpm=data['bpm'],
                            tags=data['tags'])

        return result


@api.route('/')
class ArrangementsList(Resource):
    @api.doc(description='Get an arrangements list')
    @api.expect(vk_id)
    @api.response(200, 'Success', model=arrangements_list)
    def get(self):
        json_data = request.get_json()
        user_id = json_data.get('user_id')

        try:
            try:
                if user_service.get_user(user_id) is None:
                    return {'error': 'User does not exist'}, 400
            except Exception as e:
                return {'error': str(e)}, 400

            arrangements = arrangement_service.get_user_arrangements(user_id)
            serialized_arrangements = [arrangement.to_dict() for arrangement in arrangements]
            return serialized_arrangements, 200
        except Exception as e:
            return {'error': str(e)}, 400


@api.route('/<int:arrangement_id>')
class SingleArrangement(Resource):
    @api.doc(description='Get a single arrangement')
    @api.response(200, 'Success', model=single_arrangement)
    def get(self, arrangement_id):
        try:
            arrangement = arrangement_service.get_arrangement(arrangement_id)
            if arrangement:
                return arrangement, 200
            return {'error': 'Arrangement not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


@api.route('/file/<int:arrangement_id>')
class ArrangementFile(Resource):
    @api.doc(description='Get an arrangement file', produces=['application/octet-stream'])
    @api.response(200, 'File received')
    def get(self, arrangement_id):
        arrangement = arrangement_service.get_arrangement(arrangement_id)
        file_name = arrangement.file_name
        arrangement_name = arrangement.name

        if not file_name:
            abort(404, "File not found.")

        try:
            file_data = s3_storage.get(file_name)

            if not file_data:
                abort(404, "File content is empty or not found.")

            byte_io = BytesIO(file_data)
            byte_io.seek(0)

            return send_file(
                byte_io,
                as_attachment=True,
                download_name=arrangement_name,
                mimetype='application/octet-stream'
            )
        except Exception as e:
            print(f"Error sending file: {e}")
            abort(500, "Error sending file.")
