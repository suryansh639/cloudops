#!/usr/bin/env python3
"""Comprehensive AWS Service Test for CloudOps"""
import boto3
from botocore.exceptions import ClientError
import json

def test_service(service, operation, region='us-east-1'):
    """Test a specific AWS service operation"""
    try:
        client = boto3.client(service, region_name=region)
        method = getattr(client, operation)
        response = method()
        return True, response
    except ClientError as e:
        return False, e.response['Error']['Code']
    except Exception as e:
        return False, str(e)

print("="*80)
print("CloudOps AWS Service Capability Test")
print("="*80)
print()

# Test each service with actual data
tests = [
    ("EC2 Instances", "ec2", "describe_instances", "Reservations"),
    ("EC2 Security Groups", "ec2", "describe_security_groups", "SecurityGroups"),
    ("S3 Buckets", "s3", "list_buckets", "Buckets"),
    ("CloudFront Distributions", "cloudfront", "list_distributions", "DistributionList.Items"),
    ("Lambda Functions", "lambda", "list_functions", "Functions"),
    ("RDS Instances", "rds", "describe_db_instances", "DBInstances"),
    ("DynamoDB Tables", "dynamodb", "list_tables", "TableNames"),
    ("IAM Users", "iam", "list_users", "Users"),
    ("IAM Roles", "iam", "list_roles", "Roles"),
    ("CloudWatch Metrics", "cloudwatch", "list_metrics", "Metrics"),
    ("SNS Topics", "sns", "list_topics", "Topics"),
    ("SQS Queues", "sqs", "list_queues", "QueueUrls"),
    ("Route53 Hosted Zones", "route53", "list_hosted_zones", "HostedZones"),
    ("ECS Clusters", "ecs", "list_clusters", "clusterArns"),
    ("EKS Clusters", "eks", "list_clusters", "clusters"),
]

accessible = []
denied = []
empty = []

for name, service, operation, key_path in tests:
    success, result = test_service(service, operation)
    
    if success:
        # Navigate nested keys
        data = result
        for key in key_path.split('.'):
            data = data.get(key, [])
        
        count = len(data) if isinstance(data, list) else 0
        
        if count > 0:
            accessible.append((name, count))
            print(f"✓ {name:30} {count:4} items found")
        else:
            empty.append(name)
            print(f"○ {name:30} {count:4} items (accessible, but empty)")
    else:
        denied.append((name, result))
        print(f"✗ {name:30} {result}")

print()
print("="*80)
print("Summary")
print("="*80)
print(f"✓ Services with data:     {len(accessible)}")
print(f"○ Services accessible:    {len(empty)}")
print(f"✗ Services denied:        {len(denied)}")
print(f"Total services tested:    {len(tests)}")
print()

if accessible:
    print("="*80)
    print("AWS Resources Found")
    print("="*80)
    for name, count in accessible:
        print(f"  • {name}: {count}")
    print()

# Test CloudWatch metrics in detail
print("="*80)
print("CloudWatch Metrics Sample (first 10)")
print("="*80)
success, result = test_service("cloudwatch", "list_metrics")
if success:
    for i, metric in enumerate(result.get('Metrics', [])[:10]):
        print(f"  {i+1}. {metric.get('Namespace')} - {metric.get('MetricName')}")
print()

# Test IAM users in detail
print("="*80)
print("IAM Users")
print("="*80)
success, result = test_service("iam", "list_users")
if success:
    users = result.get('Users', [])
    if users:
        for user in users:
            print(f"  • {user['UserName']} (Created: {user['CreateDate']})")
    else:
        print("  No IAM users found")
print()

# Test Security Groups
print("="*80)
print("EC2 Security Groups")
print("="*80)
success, result = test_service("ec2", "describe_security_groups")
if success:
    sgs = result.get('SecurityGroups', [])
    for sg in sgs:
        print(f"  • {sg['GroupName']} ({sg['GroupId']})")
        print(f"    Description: {sg.get('Description', 'N/A')}")
        print(f"    VPC: {sg.get('VpcId', 'N/A')}")
print()

print("="*80)
print("Conclusion")
print("="*80)
print("CloudOps can successfully access and query:")
print(f"  • {len(accessible) + len(empty)} out of {len(tests)} AWS services")
print()
print("Services with actual data:")
for name, count in accessible:
    print(f"  ✓ {name}")
print()
print("CloudOps is ready to investigate AWS resources!")
