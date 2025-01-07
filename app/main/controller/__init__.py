from ..service import vk_api_service


def extract_user_id(request) -> int:
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    access_token = auth_header.split("Bearer ")[1]

    user_id = vk_api_service.get_user_id(access_token)

    return user_id
