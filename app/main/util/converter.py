import os

from ..model.arrangements import Arrangement

host_url = os.getenv('HOST_URL')


def arrangement_to_dict(arrangement: Arrangement):
    return {
        "id": arrangement.id,
        "name": arrangement.name,
        "bpm": arrangement.bpm,
        "tags": arrangement.tags,
        "file": f'{host_url}/api/arrangements/file/{arrangement.id}',
        "created_at": arrangement.created_at.isoformat(),
        "status": arrangement.status.value
    }
