import requests, base64

print('=== Testing with real person image ===')
with open('data/images/front.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

r = requests.post('http://localhost:5001/api/process', 
    json={'front_image': 'data:image/jpeg;base64,'+b64, 'user_height': 170}, 
    timeout=180)
d = r.json()
front = d.get('results', {}).get('front', {})
mesh = front.get('mesh_data') or d.get('mesh_data')
smpl = front.get('smpl', {})
print('smplx_status:', d.get('smplx_status'))
print('smpl.success:', smpl.get('success'))
print('smpl.fit_status:', smpl.get('fit_status'))
print('smpl.fitted_to_user:', smpl.get('fitted_to_user'))
print('smpl.status_text:', smpl.get('status_text'))
if mesh:
    print('mesh_data:', 'Present,', len(mesh.get('x', [])), 'vertices')
    m = mesh.get('metadata', {})
    print('mesh_url:', m.get('mesh_url'))
    print('file_exists:', m.get('mesh_file_exists'))
    r2 = requests.get('http://localhost:5001' + m.get('mesh_url', '') + '?v=1', timeout=30)
    print('OBJ fetch: HTTP', r2.status_code, ',', len(r2.content), 'bytes')
else:
    print('mesh_data: NONE - ERROR!')
