"""Bounded wait used by API tests; all providers are mocked."""
import time


def wait_job(client, job_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        response = client.get(f'/api/jobs/{job_id}')
        assert response.status_code == 200, response.text
        job = response.json()
        if job['status'] in ('succeeded', 'failed'):
            return job
        time.sleep(.01)
    raise AssertionError('Background job did not complete')
