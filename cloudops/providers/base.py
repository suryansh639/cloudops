"""Base provider interfaces"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class CloudProvider(ABC):
    """Abstract interface for cloud providers"""
    
    @abstractmethod
    def get_cpu_metrics(self, **kwargs) -> Dict[str, Any]:
        """Get CPU metrics"""
        pass
    
    @abstractmethod
    def get_cost_data(self, **kwargs) -> Dict[str, Any]:
        """Get cost data"""
        pass
    
    @abstractmethod
    def list_security_groups(self, **kwargs) -> Dict[str, Any]:
        """List security groups"""
        pass


class KubernetesProvider(ABC):
    """Abstract interface for Kubernetes providers"""
    
    @abstractmethod
    def list_nodes(self, **kwargs) -> Dict[str, Any]:
        """List cluster nodes"""
        pass
    
    @abstractmethod
    def list_pods(self, **kwargs) -> Dict[str, Any]:
        """List pods"""
        pass
    
    @abstractmethod
    def list_deployments(self, **kwargs) -> Dict[str, Any]:
        """List deployments"""
        pass
