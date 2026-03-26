# Deployment Guide

## AWS Infrastructure
- Region: ap-southeast-2 (Sydney)
- EC2: t3.micro in public subnet
- VPC CIDR: 10.0.0.0/16
- Subnet CIDR: 10.0.1.0/24

## Starting the Server
cd smartparcel
source venv/bin/activate
gunicorn --bind 0.0.0.0:8080 --workers 4 --threads 2 app:app

## API Testing
curl http://52.64.66.38:8080/health
