import json
import os
import urllib.error
import urllib.request
from typing import Any


def request(path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], Any]:
    base = os.getenv('LEARNING_BASE_URL', 'http://127.0.0.1:8220')
    message = urllib.request.Request(base + path, headers=headers or {})
    try:
        response = urllib.request.urlopen(message, timeout=5)
    except urllib.error.HTTPError as exception:
        response = exception
    with response:
        return response.status, json.load(response), response.headers


def main() -> None:
    credential = os.getenv('LEARNING_SMOKE_CREDENTIAL', 'demo-learner-red')
    headers = {'Authorization': 'Bearer '+credential, 'X-Request-ID':'prd01-smoke'}
    health_status, health, health_headers = request('/health', headers)
    assert health_status == 200 and health == {'status':'ok','version':'0.1.0'}
    assert health_headers['X-Request-ID'] == 'prd01-smoke'
    status, content, _ = request('/v1/content', headers)
    assert status == 200 and [item['id'] for item in content['items']] == ['content-red-approved']
    status, progress, _ = request('/v1/learners/learner-red-1/progress', headers)
    assert status == 200 and progress['learner_id'] == 'learner-red-1'
    for learner_id in ['learner-red-2', 'learner-blue-1', 'learner-missing']:
        status, denied, _ = request(f'/v1/learners/{learner_id}/progress', headers)
        assert status == 404 and denied['error']['code'] == 'not_found'
        assert 'completion_percent' not in json.dumps(denied)
    spoofed = headers | {'X-Tenant-ID':'tenant-blue','X-User-ID':'learner-blue-1','X-Role':'admin'}
    assert request('/v1/learners/learner-blue-1/progress', spoofed)[0] == 404
    assert request('/v1/content')[0] == 401
    assert request('/v1/content?limit=21', headers)[0] == 422
    assert request('/v1/learners/invalid%20id/progress', headers)[0] == 422
    assert '/v1/content' in request('/openapi.json')[1]['paths']
    print('PRD 01 HTTP smoke: 11 scenarios passed; protected foreign data absent')


if __name__ == '__main__':
    main()