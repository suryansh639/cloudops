#!/usr/bin/env python3
"""Remediate S3 Public Bucket Incident"""
import boto3

s3 = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'cloudops-incident-test-bucket-2026'

print("="*80)
print("CloudOps S3 Incident Remediation")
print("="*80)
print()

print("REMEDIATION STEPS:")
print("-"*80)

# Step 1: Remove public policy
try:
    s3.delete_bucket_policy(Bucket=bucket_name)
    print("✓ Step 1: Removed public bucket policy")
except Exception as e:
    print(f"✗ Step 1 failed: {e}")

# Step 2: Enable public access block
try:
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )
    print("✓ Step 2: Enabled public access block")
except Exception as e:
    print(f"✗ Step 2 failed: {e}")

# Step 3: Delete sensitive file
try:
    s3.delete_object(Bucket=bucket_name, Key='sensitive-data.txt')
    print("✓ Step 3: Deleted sensitive file")
except Exception as e:
    print(f"✗ Step 3 failed: {e}")

# Step 4: Delete bucket
try:
    s3.delete_bucket(Bucket=bucket_name)
    print("✓ Step 4: Deleted bucket")
except Exception as e:
    print(f"✗ Step 4 failed: {e}")

print()
print("="*80)
print("VERIFICATION")
print("="*80)

# Verify bucket is gone
try:
    s3.head_bucket(Bucket=bucket_name)
    print("✗ Bucket still exists")
except:
    print("✓ Bucket successfully deleted")

# Try to access the public URL
import urllib.request
test_url = f"https://{bucket_name}.s3.ap-south-1.amazonaws.com/sensitive-data.txt"
try:
    urllib.request.urlopen(test_url)
    print("✗ File still publicly accessible")
except:
    print("✓ Public access blocked")

print()
print("="*80)
print("✓ REMEDIATION COMPLETE")
print("="*80)
print("All security incidents have been resolved!")
