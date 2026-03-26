# Troubleshooting Log

## Issue 1 - EC2 Instance Connect Failed
Problem: Browser-based SSH connection failed repeatedly
Solution: Used SSH client with .pem key pair via PowerShell
Command: ssh -i "smartparcel-key.pem" ec2-user@52.64.66.38

## Issue 2 - SQS Queue Name Typo
Problem: Queue created as "martparcel" instead of "smartparcel"
Solution: Deleted wrong queue, recreated with correct name
New URL: https://sqs.ap-southeast-2.amazonaws.com/848125594279/smartparcel-notifications-20210001636

## Issue 3 - pip Install on Amazon Linux 2023
Problem: pip install failed with RECORD file not found
Solution: Used Python virtual environment
Commands:
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

## Issue 4 - Git Push Rejected
Problem: Remote contained README not in local repo
Solution: Used force push
Command: git push -u origin main --force

## Issue 5 - PowerShell .pem File Not Found
Problem: .pem file stored in OneDrive not local Desktop
Solution: Used full OneDrive path
Command: ssh -i "C:\Users\Charl\OneDrive\Desktop\smartparcel-key.pem" ec2-user@52.64.66.38

## Issue 6 - Lambda Not Receiving SQS Messages
Problem: Messages were stuck in SQS queue, Lambda not triggered
Cause: Lambda trigger was connected to old deleted queue (martparcel)
Solution: Deleted old Lambda trigger, added new trigger pointing to
          correct queue: smartparcel-notifications-20210001636
Result: SQS to Lambda to SNS email pipeline working correctly

## Issue 7 - SQS Queue Name Typo
Problem: Original SQS queue created as martparcel instead of smartparcel
Cause: Typing error during queue creation
Solution: Deleted wrong queue, recreated with correct name
Result: Full notification pipeline working correctly
