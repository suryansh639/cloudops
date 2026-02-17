"""Mock provider implementations"""
from typing import Dict, Any
from cloudops.providers.base import CloudProvider, KubernetesProvider


class MockCloudProvider(CloudProvider):
    """Mock cloud provider for testing"""
    
    def get_cpu_metrics(self, **kwargs) -> Dict[str, Any]:
        return {
            "datapoints": [
                {"timestamp": "2026-02-17T10:00:00Z", "average": 92.3},
                {"timestamp": "2026-02-17T09:00:00Z", "average": 45.0}
            ]
        }
    
    def get_cost_data(self, **kwargs) -> Dict[str, Any]:
        return {
            "total": 1250.45,
            "by_service": {
                "EC2": 650.20,
                "RDS": 300.15,
                "S3": 200.10,
                "Other": 100.00
            }
        }
    
    def list_security_groups(self, **kwargs) -> Dict[str, Any]:
        return {
            "security_groups": [
                {
                    "id": "sg-12345",
                    "name": "web-servers",
                    "rules": [
                        {"protocol": "tcp", "port": 80, "source": "0.0.0.0/0"}
                    ]
                }
            ]
        }


class MockK8sProvider(KubernetesProvider):
    """Mock Kubernetes provider for testing"""
    
    def list_nodes(self, **kwargs) -> Dict[str, Any]:
        return {
            "nodes": [
                {"name": "node-1", "cpu": "95%", "memory": "70%"},
                {"name": "node-2", "cpu": "45%", "memory": "60%"},
                {"name": "node-3", "cpu": "50%", "memory": "55%"}
            ]
        }
    
    def list_pods(self, **kwargs) -> Dict[str, Any]:
        return {
            "pods": [
                {"name": "api-gateway-7d8f9", "namespace": "prod", "cpu": "3.2", "memory": "2.1Gi"},
                {"name": "worker-abc123", "namespace": "prod", "cpu": "1.5", "memory": "1.8Gi"}
            ]
        }
    
    def list_deployments(self, **kwargs) -> Dict[str, Any]:
        return {
            "deployments": [
                {"name": "api-gateway", "version": "v2.3.1", "deployed_at": "2026-02-17T09:00:00Z"}
            ]
        }
