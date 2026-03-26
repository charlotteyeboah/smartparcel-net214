# -------------------------------------------------------
# SmartParcel — NET_214 Project, Spring 2026
# Author  : Charlotte Yeboah
# ID      : 20210001636
# Email   : 20210001636@students.cud.ac.ae
# AWS Acc : 848125594279
# -------------------------------------------------------

from flask import Flask, request, jsonify
import boto3
import json
import uuid
import datetime
import socket

app = Flask(__name__)

# AWS Configuration
REGION = 'ap-southeast-2'
DYNAMODB_TABLE = 'smartparcel-parcels'
S3_BUCKET = 'smartparcel-photos-20210001636'
SQS_QUEUE_URL = 'https://sqs.ap-southeast-2.amazonaws.com/848125594279/smartparcel-notifications-20210001636'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-southeast-2:848125594279:smartparcel-alerts-20210001636'

# AWS Clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
sqs = boto3.client('sqs', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

table = dynamodb.Table(DYNAMODB_TABLE)

# API Keys for authentication
API_KEYS = {
    'key-admin-001': 'admin',
    'key-driver-001': 'driver',
    'key-customer-001': 'customer'
}

def get_role(request):
    api_key = request.headers.get('X-API-Key')
    return API_KEYS.get(api_key)

def require_auth(*allowed_roles):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            role = get_role(request)
            if not role:
                return jsonify({'error': 'Unauthorized'}), 401
            if allowed_roles and role not in allowed_roles:
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_input(data, required_fields):
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f'Missing required field: {field}'
    injection_patterns = ["'", "DROP", "SELECT", "INSERT", "DELETE", "--"]
    for field in required_fields:
        if field in data:
            for pattern in injection_patterns:
                if pattern.upper() in str(data[field]).upper():
                    return False, f'Invalid input detected in {field}'
    return True, None

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'hostname': socket.gethostname()
    }), 200

# POST /api/parcels
@app.route('/api/parcels', methods=['POST'])
@require_auth('admin', 'driver')
def create_parcel():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400

        valid, error = validate_input(data, ['sender', 'receiver', 'address', 'customer_email'])
        if not valid:
            return jsonify({'error': error}), 400

        parcel_id = f'PKG-2026-{str(uuid.uuid4())[:8].upper()}'
        timestamp = datetime.datetime.utcnow().isoformat()

        item = {
            'parcel_id': parcel_id,
            'sender': data['sender'],
            'receiver': data['receiver'],
            'address': data['address'],
            'customer_email': data['customer_email'],
            'status': 'pending',
            'history': [{'status': 'pending', 'timestamp': timestamp}],
            'created_at': timestamp
        }

        table.put_item(Item=item)

        return jsonify({'parcel_id': parcel_id, 'status': 'pending'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /api/parcels/<id>
@app.route('/api/parcels/<parcel_id>', methods=['GET'])
@require_auth('admin', 'driver', 'customer')
def get_parcel(parcel_id):
    try:
        response = table.get_item(Key={'parcel_id': parcel_id})
        item = response.get('Item')
        if not item:
            return jsonify({'error': 'Parcel not found'}), 404
        return jsonify(item), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PUT /api/parcels/<id>/status
@app.route('/api/parcels/<parcel_id>/status', methods=['PUT'])
@require_auth('driver')
def update_status(parcel_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400

        valid_statuses = ['picked_up', 'in_transit', 'delivered']
        new_status = data.get('status')

        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of {valid_statuses}'}), 400

        response = table.get_item(Key={'parcel_id': parcel_id})
        item = response.get('Item')

        if not item:
            return jsonify({'error': 'Parcel not found'}), 404

        if item['status'] == 'cancelled':
            return jsonify({'error': 'Cannot update cancelled parcel'}), 409

        timestamp = datetime.datetime.utcnow().isoformat()
        history = item.get('history', [])
        history.append({'status': new_status, 'timestamp': timestamp})

        table.update_item(
            Key={'parcel_id': parcel_id},
            UpdateExpression='SET #s = :s, history = :h',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': new_status, ':h': history}
        )

        # Send SQS message
        message = {
            'parcel_id': parcel_id,
            'new_status': new_status,
            'customer_email': item.get('customer_email', ''),
            'driver_name': get_role(request),
            'timestamp': timestamp
        }
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message)
        )

        return jsonify({'parcel_id': parcel_id, 'status': new_status}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /api/parcels
@app.route('/api/parcels', methods=['GET'])
@require_auth('admin')
def list_parcels():
    try:
        status_filter = request.args.get('status')

        if status_filter:
            response = table.query(
                IndexName='status-index',
                KeyConditionExpression='#s = :s',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': status_filter}
            )
        else:
            response = table.scan()

        return jsonify(response['Items']), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE /api/parcels/<id>
@app.route('/api/parcels/<parcel_id>', methods=['DELETE'])
@require_auth('admin')
def cancel_parcel(parcel_id):
    try:
        response = table.get_item(Key={'parcel_id': parcel_id})
        item = response.get('Item')

        if not item:
            return jsonify({'error': 'Parcel not found'}), 404

        if item['status'] in ['picked_up', 'in_transit', 'delivered']:
            return jsonify({'error': 'Cannot cancel parcel that is already picked up or later'}), 409

        timestamp = datetime.datetime.utcnow().isoformat()
        history = item.get('history', [])
        history.append({'status': 'cancelled', 'timestamp': timestamp})

        table.update_item(
            Key={'parcel_id': parcel_id},
            UpdateExpression='SET #s = :s, history = :h',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'cancelled', ':h': history}
        )

        return jsonify({'parcel_id': parcel_id, 'status': 'cancelled'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST /api/parcels/<id>/photo
@app.route('/api/parcels/<parcel_id>/photo', methods=['POST'])
@require_auth('driver')
def upload_photo(parcel_id):
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400

        photo = request.files['photo']
        key = f'{parcel_id}/proof.jpg'

        s3.upload_fileobj(photo, S3_BUCKET, key)
        photo_url = f's3://{S3_BUCKET}/{key}'

        table.update_item(
            Key={'parcel_id': parcel_id},
            UpdateExpression='SET photo_url = :p',
            ExpressionAttributeValues={':p': photo_url}
        )

        return jsonify({'parcel_id': parcel_id, 'photo_url': photo_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
