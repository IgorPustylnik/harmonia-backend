from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from flask import request, send_file
from flask_restx import Resource, reqparse
from .. import s3_storage
from ..model.arrangement_status import ArrangementStatus
from ..util import converter
from ..util.decorator import require_access_token
from ..util.dto import ArrangementDTO
from ..service.database import arrangement_service, user_service
from ..service import vk_api_service, audio_to_video_service
from ..controller import websocket_controller

api = ArrangementDTO().api
create_arrangement = ArrangementDTO().create_arrangement
create_arrangement_response = ArrangementDTO().create_arrangement_response
single_arrangement = ArrangementDTO().arrangement
rename_arrangement = ArrangementDTO().rename_arrangement
arrangements_list = ArrangementDTO().arrangements_list
upload_video = ArrangementDTO().upload_video

executor = ThreadPoolExecutor(max_workers=5)


@api.route('/create')
class CreateArrangement(Resource):
    # For Swagger only
    upload_parser = reqparse.RequestParser()
    upload_parser.add_argument('name', type=str, location='form', required=True, help="Name of the arrangement")
    upload_parser.add_argument('tags', type=str, location='form', required=True,
                               help="Tags for desired melody")
    upload_parser.add_argument('bpm', type=int, location='form', required=True, help="BPM")
    upload_parser.add_argument('file', type='file', location='files', required=True, help="The drums file")

    @api.doc(description='Create an arrangement', security='access_token')
    @api.expect(upload_parser)
    @api.response(201, 'Success', model=create_arrangement_response)
    @require_access_token
    def post(self, user_id):
        if 'file' not in request.files:
            return {'error': 'No file part in the request'}, 400

        file = request.files['file']

        name = request.form.get('name')
        tags = request.form.get('tags')
        bpm = float(request.form.get('bpm'))

        data = {"user_id": user_id, "name": name, "tags": tags, "bpm": bpm}

        result = arrangement_service.add_arrangement(data)

        if result[1] == 201:
            websocket_controller.data_updated(user_id)
            arrangement_id = int(result[0]['id'])
            drums_bytes = bytes(file.read())
            executor.submit(arrangement_service.create_music,
                            arrangement_id=arrangement_id,
                            drums_bytes=drums_bytes,
                            bpm=bpm,
                            tags=tags,
                            websocket_status_update_handler=lambda: websocket_controller.data_updated(user_id))

        return result


@api.route('/')
class ArrangementsList(Resource):
    @api.doc(description='Get an arrangements list', security='access_token',
             params={'page': {'description': 'Number of page', 'type': 'integer'},
                     'search_query': {'description': 'Search query', 'type': 'string'},
                     'status': {'description': 'Arrangement status (list separated by commas)', 'type': 'string'}})
    @api.response(200, 'Success', model=arrangements_list)
    @require_access_token
    def get(self, user_id):
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search_query', '', type=str)
        status_string = request.args.get('status', '', type=str)
        status = [ArrangementStatus(s.upper()) for s in status_string.split(',') if status_string != '']
        try:
            try:
                if user_service.get_user(user_id) is None:
                    return {'error': 'User does not exist'}, 400
            except Exception as e:
                return {'error': str(e)}, 400

            arrangements = arrangement_service.get_user_arrangements(user_id, page, search_query, status)
            return arrangements
        except Exception as e:
            return {'error': str(e)}, 400


@api.route('/<int:arrangement_id>')
class Arrangement(Resource):
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

    @api.doc(description='Rename an arrangement', security='access_token')
    @api.response(200, 'Success')
    @api.expect(rename_arrangement)
    @require_access_token
    def patch(self, user_id, arrangement_id):
        arrangement = arrangement_service.get_arrangement(arrangement_id)

        if arrangement and arrangement.user_id == user_id:
            arrangement.name = request.json.get('name')
            return arrangement_service.update_arrangement(arrangement)
        elif arrangement:
            return {'error': 'Access denied'}, 403

        return {'error': 'Arrangement not found'}, 404

    @api.doc(description='Delete an arrangement', security='access_token')
    @api.response(200, 'Success')
    @require_access_token
    def delete(self, user_id, arrangement_id):
        arrangement = arrangement_service.get_arrangement(arrangement_id)

        if arrangement and arrangement.user_id == user_id:
            return arrangement_service.delete_arrangement(arrangement_id)
        elif arrangement:
            return {'error': 'Access denied'}, 403

        return {'error': 'Arrangement not found'}, 404


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


@api.route('/upload_video/<int:arrangement_id>')
class ArrangementShare(Resource):
    @api.doc(description='Upload arrangement to VK as a video. Upload link must be provided.', security='access_token')
    @api.response(200, 'Link received')
    @api.expect(upload_video)
    @require_access_token
    def post(self, user_id, arrangement_id):

        url = request.json.get('url')
        if url is None:
            return {'error': 'Missing url'}, 400
        arrangement = arrangement_service.get_arrangement(arrangement_id)

        if arrangement and arrangement.user_id == user_id:

            audio_bytes = s3_storage.get(arrangement.file_name)
            video_bytes = audio_to_video_service.convert_audio_to_video(audio_bytes)
            response = vk_api_service.upload_video(url, video_bytes)
            return response.json(), response.status_code
        elif arrangement:
            return {'error': 'Access denied'}, 403

        return {'error': 'Arrangement not found'}, 404
