# SmartParcel — NET214 Cloud-Native Parcel Tracking System

A cloud-native parcel tracking REST API built with Flask, deployed on AWS.

## AWS Services Used
- EC2 (Flask + Gunicorn server)
- DynamoDB (parcel database)
- S3 (delivery photos)
- SQS (message queue)
- Lambda (notification processor)
- SNS (email alerts)
- CloudWatch (monitoring)

## Installation
pip install -r requirements.txt

## Running the Server
gunicorn --bind 0.0.0.0:8080 --workers 4 --threads 2 app:app

## API Endpoints
- POST   /api/parcels              - Create parcel
- GET    /api/parcels/<id>         - Get parcel
- PUT    /api/parcels/<id>/status  - Update status
- GET    /api/parcels              - List parcels (admin)
- DELETE /api/parcels/<id>         - Cancel parcel (admin)
- GET    /health                   - Health check

## Authentication
Include X-API-Key header:
- key-admin-001    (admin role)
- key-driver-001   (driver role)
- key-customer-001 (customer role)
