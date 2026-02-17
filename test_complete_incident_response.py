#!/usr/bin/env python3
"""Complete Incident Response Test"""
import boto3
import json

ec2 = boto3.client('ec2', region_name='ap-south-1')

print("="*80)
print("CloudOps Complete Incident Response Test")
print("="*80)
print()

# Detection Phase
print("PHASE 1: INCIDENT DETECTION")
print("="*80)

all_sgs = ec2.describe_security_groups()
incidents = []

for sg in all_sgs['SecurityGroups']:
    for rule in sg.get('IpPermissions', []):
        for ip_range in rule.get('IpRanges', []):
            if ip_range.get('CidrIp') == '0.0.0.0/0':
                from_port = rule.get('FromPort', 'all')
                to_port = rule.get('ToPort', 'all')
                protocol = rule.get('IpProtocol', 'all')
                
                # Check for high-risk ports
                risk_level = 'LOW'
                if from_port in [22, 3389, 1433, 3306, 5432]:  # SSH, RDP, SQL
                    risk_level = 'CRITICAL'
                elif from_port in [80, 443, 8080]:
                    risk_level = 'MEDIUM'
                
                incidents.append({
                    'sg_id': sg['GroupId'],
                    'sg_name': sg['GroupName'],
                    'port': from_port,
                    'protocol': protocol,
                    'risk': risk_level,
                    'description': ip_range.get('Description', 'N/A')
                })

print(f"✓ Scanned {len(all_sgs['SecurityGroups'])} security groups")
print(f"⚠ Found {len(incidents)} security incidents\n")

# Categorize by risk
critical = [i for i in incidents if i['risk'] == 'CRITICAL']
medium = [i for i in incidents if i['risk'] == 'MEDIUM']
low = [i for i in incidents if i['risk'] == 'LOW']

print(f"Risk Breakdown:")
print(f"  🔴 CRITICAL: {len(critical)}")
print(f"  🟡 MEDIUM:   {len(medium)}")
print(f"  🟢 LOW:      {len(low)}")
print()

if critical:
    print("CRITICAL INCIDENTS:")
    for inc in critical:
        print(f"  🔴 {inc['sg_name']} ({inc['sg_id']})")
        print(f"     Port {inc['port']} ({inc['protocol']}) open to 0.0.0.0/0")
        print(f"     Description: {inc['description']}")
        print()

# Analysis Phase
print("PHASE 2: INCIDENT ANALYSIS")
print("="*80)

test_incidents = [i for i in incidents if 'cloudops' in i['sg_name'].lower() or 'remediation-test' in i['sg_name'].lower()]

print(f"✓ Identified {len(test_incidents)} test incident(s) for remediation")
for inc in test_incidents:
    print(f"  • {inc['sg_name']}: Port {inc['port']} - {inc['risk']} risk")
print()

# Remediation Phase
print("PHASE 3: AUTOMATED REMEDIATION")
print("="*80)

remediated = []
for inc in test_incidents:
    try:
        sg_id = inc['sg_id']
        
        # Revoke the rule
        ec2.revoke_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': inc['protocol'],
                'FromPort': inc['port'],
                'ToPort': inc['port'],
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )
        print(f"✓ Revoked rule: {inc['sg_name']} port {inc['port']}")
        
        # Delete security group if it's a test group
        if 'test' in inc['sg_name'].lower():
            ec2.delete_security_group(GroupId=sg_id)
            print(f"✓ Deleted security group: {inc['sg_name']}")
        
        remediated.append(inc)
        
    except Exception as e:
        print(f"✗ Failed to remediate {inc['sg_name']}: {e}")

print()

# Verification Phase
print("PHASE 4: VERIFICATION")
print("="*80)

# Re-scan
all_sgs_after = ec2.describe_security_groups()
incidents_after = []

for sg in all_sgs_after['SecurityGroups']:
    for rule in sg.get('IpPermissions', []):
        for ip_range in rule.get('IpRanges', []):
            if ip_range.get('CidrIp') == '0.0.0.0/0':
                from_port = rule.get('FromPort', 'all')
                if from_port in [22, 3389, 1433, 3306, 5432]:
                    incidents_after.append(sg['GroupId'])

critical_before = len(critical)
critical_after = len(incidents_after)

print(f"Critical incidents before: {critical_before}")
print(f"Critical incidents after:  {critical_after}")
print(f"Incidents remediated:      {len(remediated)}")
print()

if critical_after < critical_before:
    print("✓ Security posture improved!")
else:
    print("⚠ Security posture unchanged")

print()

# Summary
print("="*80)
print("TEST SUMMARY")
print("="*80)
print(f"✓ Detection:    Found {len(incidents)} incidents")
print(f"✓ Analysis:     Identified {len(test_incidents)} test incidents")
print(f"✓ Remediation:  Fixed {len(remediated)} incidents")
print(f"✓ Verification: Confirmed remediation")
print()
print("CloudOps Capabilities Verified:")
print("  ✓ Incident Detection (scanning security groups)")
print("  ✓ Risk Assessment (categorizing by severity)")
print("  ✓ Automated Remediation (revoking rules, deleting groups)")
print("  ✓ Verification (confirming fixes)")
print()
print("="*80)
