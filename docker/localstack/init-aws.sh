#!/bin/bash
set -euo pipefail

echo "Provisioning LocalStack S3 and SQS..."

awslocal s3 mb s3://regimpact-documents 2>/dev/null || true
awslocal sqs create-queue --queue-name regimpact-jobs >/dev/null
awslocal sqs create-queue --queue-name regimpact-jobs-dlq >/dev/null

echo "S3 buckets:"
awslocal s3 ls
echo "SQS queues:"
awslocal sqs list-queues
echo "LocalStack init complete."
