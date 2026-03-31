import concurrent.futures
import requests
import time

BASE_URL = 'http://52.64.66.38:8080'

def make_health_request(i):
    start = time.time()
    resp = requests.get(f'{BASE_URL}/health')
    elapsed = time.time() - start
    return {'id': i, 'status': resp.status_code, 'time': round(elapsed, 3)}

def make_post_request(i):
    start = time.time()
    resp = requests.post(
        f'{BASE_URL}/api/parcels',
        json={'sender': f'Sender {i}', 'receiver': f'Receiver {i}', 'address': 'Dubai', 'customer_email': 'charlotte@students.cud.ac.ae'},
        headers={'X-API-Key': 'key-driver-001'}
    )
    elapsed = time.time() - start
    return {'id': i, 'status': resp.status_code, 'time': round(elapsed, 3)}

print('=== Test 1: GET /health ===')
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    results = list(pool.map(make_health_request, range(20)))
for r in results:
    print(f"Request {r['id']}: {r['status']} in {r['time']}s")

print('\n=== Test 2: POST /api/parcels ===')
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    results = list(pool.map(make_post_request, range(20)))
for r in results:
    print(f"Request {r['id']}: {r['status']} in {r['time']}s")
