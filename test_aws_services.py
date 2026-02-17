#!/usr/bin/env python3
"""Test CloudOps access to various AWS services"""
import boto3
from botocore.exceptions import ClientError

services_to_test = [
    ('ec2', 'describe_instances', 'us-east-1', 'Reservations'),
    ('s3', 'list_buckets', 'us-east-1', 'Buckets'),
    ('cloudfront', 'list_distributions', 'us-east-1', 'DistributionList'),
    ('lambda', 'list_functions', 'us-east-1', 'Functions'),
    ('rds', 'describe_db_instances', 'us-east-1', 'DBInstances'),
    ('dynamodb', 'list_tables', 'us-east-1', 'TableNames'),
    ('iam', 'list_users', 'us-east-1', 'Users'),
    ('cloudwatch', 'list_metrics', 'us-east-1', 'Metrics'),
    ('sns', 'list_topics', 'us-east-1', 'Topics'),
    ('sqs', 'list_queues', 'us-east-1', 'QueueUrls'),
    ('elasticloadbalancing', 'describe_load_balancers', 'us-east-1', 'LoadBalancers'),
    ('route53', 'list_hosted_zones', 'us-east-1', 'HostedZones'),
]

print("="*70)
print("AWS Services Access Test")
print("="*70)

results = []
for service, operation, region, key in services_to_test:
    try:
        client = boto3.client(service, region_name=region)
        method = getattr(client, operation)
        response = method()
        
        # Get count
        if key in response:
            data = response[key]
            count = len(data) if isinstance(data, list) else len(data.get('Items', []))
        else:
            count = 0
        
        results.append((service.upper(), '✓', f"{count} items"))
        print(f"✓ {service.upper():25} {count} items")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            results.append((service.upper(), '✗', 'Access Denied'))
            print(f"✗ {service.upper():25} Access Denied")
        else:
            results.append((service.upper(), '⚠', error_code))
            print(f"⚠ {service.upper():25} {error_code}")
    except Exception as e:
        results.append((service.upper(), '✗', str(e)[:30]))
        print(f"✗ {service.upper():25} {str(e)[:30]}")

print("\n" + "="*70)
print("Summary")
print("="*70)

accessible = sum(1 for _, status, _ in results if status == '✓')
denied = sum(1 for _, status, _ in results if status == '✗')
other = sum(1 for _, status, _ in results if status == '⚠')

print(f"✓ Accessible: {accessible}/{len(results)}")
print(f"✗ Denied: {denied}/{len(results)}")
print(f"⚠ Other: {other}/{len(results)}")

print("\n" + "="*70)
print("CloudOps can query these AWS services:")
print("="*70)
for service, status, info in results:
    if status == '✓':
        print(f"  • {service}: {info}")
