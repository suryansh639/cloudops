"""AWS provider implementation"""
from typing import Dict, Any
from datetime import datetime, timedelta
from cloudops.providers.base import CloudProvider

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSProvider(CloudProvider):
    """AWS cloud provider implementation"""
    
    def __init__(self, session=None):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 not installed")
        
        self.session = session or boto3.Session()
        self.ec2 = self.session.client('ec2')
        self.cloudwatch = self.session.client('cloudwatch')
        self.ce = self.session.client('ce')
        self.config_service = self.session.client('config')
    
    def get_cpu_metrics(self, **kwargs) -> Dict[str, Any]:
        """Get CPU metrics from CloudWatch"""
        metric = kwargs.get("metric", "CPUUtilization")
        period = kwargs.get("period", 3600)
        stat = kwargs.get("stat", "Average")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=period)
        
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=[stat]
            )
            
            return {
                "datapoints": [
                    {
                        "timestamp": dp['Timestamp'].isoformat(),
                        "average": dp.get(stat, 0)
                    }
                    for dp in response['Datapoints']
                ]
            }
        except (ClientError, BotoCoreError) as e:
            raise Exception(f"AWS CloudWatch error: {str(e)}")
    
    def get_cost_data(self, **kwargs) -> Dict[str, Any]:
        """Get cost data from Cost Explorer"""
        end = datetime.utcnow().date()
        start = end - timedelta(days=30)
        
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start.isoformat(),
                    'End': end.isoformat()
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            by_service = {}
            total = 0.0
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_service[service] = by_service.get(service, 0) + cost
                    total += cost
            
            return {
                "total": round(total, 2),
                "by_service": {k: round(v, 2) for k, v in by_service.items()}
            }
        except (ClientError, BotoCoreError) as e:
            raise Exception(f"AWS Cost Explorer error: {str(e)}")
    
    def list_security_groups(self, **kwargs) -> Dict[str, Any]:
        """List EC2 security groups"""
        try:
            response = self.ec2.describe_security_groups()
            
            return {
                "security_groups": [
                    {
                        "id": sg['GroupId'],
                        "name": sg['GroupName'],
                        "rules": [
                            {
                                "protocol": rule.get('IpProtocol', 'all'),
                                "port": rule.get('FromPort', 'all'),
                                "source": rule['IpRanges'][0]['CidrIp'] if rule.get('IpRanges') else 'N/A'
                            }
                            for rule in sg.get('IpPermissions', [])
                        ]
                    }
                    for sg in response['SecurityGroups']
                ]
            }
        except (ClientError, BotoCoreError) as e:
            raise Exception(f"AWS EC2 error: {str(e)}")
