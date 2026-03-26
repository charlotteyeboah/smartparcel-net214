import concurrent.futures
import requests
import time

BASE_URL = 'http://52.64.66.38:8080'

def make_request(i):
    start = time.time()
    resp = requests.get(f'{BASE_URL}/health')
    elapsed = time.time() - start
    return {'id': i, 'status': resp.status_code, 'time': round(elapsed, 3)}

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    results = list(pool.map(make_request, range(20)))

for r in results:
    print(f"Request {r['id']}: {r['status']} in {r['time']}s")
