"""Authentication module for cloud providers"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSAuth:
    """AWS authentication using STS AssumeRole"""
    
    def __init__(self, config):
        self.config = config
        self.cache_file = Path.home() / ".cloudops" / "aws_credentials.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_credentials(self):
        """Get AWS credentials, using cache if valid"""
        # Check cache first
        cached = self._load_cached_credentials()
        if cached and self._is_valid(cached):
            return cached
        
        # Get new credentials
        role_arn = self.config.get("cloud.aws.role_arn")
        if role_arn:
            creds = self._assume_role(role_arn)
        else:
            creds = self._get_default_credentials()
        
        # Cache credentials
        self._cache_credentials(creds)
        return creds
    
    def _assume_role(self, role_arn: str) -> dict:
        """Assume IAM role using STS"""
        if not BOTO3_AVAILABLE:
            raise Exception("boto3 not installed")
        
        session_name = f"cloudops-{os.getenv('USER', 'unknown')}"
        duration = self.config.get("cloud.aws.session_duration", 3600)
        
        sts = boto3.client('sts')
        
        try:
            response = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration
            )
            
            creds = response['Credentials']
            return {
                "access_key": creds['AccessKeyId'],
                "secret_key": creds['SecretAccessKey'],
                "session_token": creds['SessionToken'],
                "expiration": creds['Expiration'].isoformat()
            }
        
        except ClientError as e:
            raise Exception(f"Failed to assume role: {e}")
    
    def _get_default_credentials(self) -> dict:
        """Get credentials from default AWS credential chain"""
        if not BOTO3_AVAILABLE:
            raise Exception("boto3 not installed")
        
        session = boto3.Session()
        creds = session.get_credentials()
        
        if not creds:
            raise Exception("No AWS credentials found")
        
        return {
            "access_key": creds.access_key,
            "secret_key": creds.secret_key,
            "session_token": creds.token,
            "expiration": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
    
    def _load_cached_credentials(self) -> dict:
        """Load credentials from cache"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                return json.load(f)
        except:
            return None
    
    def _cache_credentials(self, creds: dict):
        """Cache credentials to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(creds, f)
        
        # Set restrictive permissions
        os.chmod(self.cache_file, 0o600)
    
    def _is_valid(self, creds: dict) -> bool:
        """Check if cached credentials are still valid"""
        if not creds or 'expiration' not in creds:
            return False
        
        expiration = datetime.fromisoformat(creds['expiration'].rstrip('Z'))
        # Consider valid if more than 5 minutes remaining
        return expiration > datetime.utcnow() + timedelta(minutes=5)
    
    def get_session(self):
        """Get boto3 session with credentials"""
        if not BOTO3_AVAILABLE:
            raise Exception("boto3 not installed")
        
        creds = self.get_credentials()
        
        return boto3.Session(
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds.get('session_token')
        )


class AzureAuth:
    """Azure authentication (placeholder for Phase 2)"""
    
    def __init__(self, config):
        self.config = config
    
    def get_credentials(self):
        raise NotImplementedError("Azure auth not implemented yet")


class GCPAuth:
    """GCP authentication (placeholder for Phase 2)"""
    
    def __init__(self, config):
        self.config = config
    
    def get_credentials(self):
        raise NotImplementedError("GCP auth not implemented yet")
