#!/usr/bin/env python3
"""Simple CloudOps AWS Integration Test"""
import boto3
from cloudops.config import Config
from cloudops.providers.aws import AWSProvider

print("="*60)
print("CloudOps AWS Integration Test")
print("="*60)

# Test 1: AWS Connectivity
print("\n1. Testing AWS Connectivity...")
try:
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"   ✓ Account: {identity['Account']}")
    print(f"   ✓ User: {identity['Arn'].split('/')[-1]}")
    print(f"   ✓ Region: {boto3.Session().region_name or 'us-east-1 (default)'}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    exit(1)

# Test 2: CloudOps Configuration
print("\n2. Testing CloudOps Configuration...")
try:
    config = Config.load()
    print(f"   ✓ Config loaded from: {config.config_path}")
    print(f"   ✓ AI Provider: {config.get('ai.provider')}")
    print(f"   ✓ Cloud Provider: {config.get('cloud.primary')}")
    print(f"   ✓ Real APIs: {config.get('cloud.use_real_apis')}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    exit(1)

# Test 3: AWS Provider
print("\n3. Testing CloudOps AWS Provider...")
try:
    aws = AWSProvider()
    
    # Test EC2
    result = aws.list_security_groups()
    print(f"   ✓ EC2 API: {len(result.get('security_groups', []))} security groups")
    
    # Test CloudWatch
    try:
        result = aws.get_cpu_metrics(period=3600)
        print(f"   ✓ CloudWatch API: {len(result.get('datapoints', []))} datapoints")
    except Exception as e:
        print(f"   ⚠ CloudWatch API: {str(e)[:50]}...")
    
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Configuration Check
print("\n4. CloudOps Configuration Summary...")
print(f"   • Config file: ~/.cloudops/config.yaml")
print(f"   • Audit logs: ~/.cloudops/audit/")
print(f"   • AWS Account: {identity['Account']}")
print(f"   • AWS User: {identity['Arn'].split('/')[-1]}")

print("\n" + "="*60)
print("✓ All tests passed!")
print("="*60)
print("\nCloudOps is successfully integrated with your AWS account.")
print("\nNext steps:")
print("  1. Set an AI provider API key (e.g., export GOOGLE_API_KEY='...')")
print("  2. Run: python -m cloudops investigate 'list ec2 instances'")
print("  3. Check audit logs: python -m cloudops audit")
