"""Kubernetes provider implementation"""
from typing import Dict, Any
from cloudops.providers.base import KubernetesProvider

try:
    from kubernetes import client, config as k8s_config
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class K8sProvider(KubernetesProvider):
    """Kubernetes provider implementation"""
    
    def __init__(self):
        if not K8S_AVAILABLE:
            raise ImportError("kubernetes client not installed")
        
        k8s_config.load_kube_config()
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()
    
    def list_nodes(self, **kwargs) -> Dict[str, Any]:
        """List cluster nodes"""
        try:
            nodes = self.core.list_node()
            return {
                "nodes": [
                    {
                        "name": node.metadata.name,
                        "cpu": self._get_node_cpu(node),
                        "memory": self._get_node_memory(node)
                    }
                    for node in nodes.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Kubernetes API error: {e.reason}")
    
    def list_pods(self, **kwargs) -> Dict[str, Any]:
        """List pods"""
        namespace = kwargs.get("namespace", "default")
        all_ns = kwargs.get("all_namespaces", False)
        
        try:
            if all_ns:
                pods = self.core.list_pod_for_all_namespaces()
            else:
                pods = self.core.list_namespaced_pod(namespace)
            
            return {
                "pods": [
                    {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "cpu": self._get_pod_cpu(pod),
                        "memory": self._get_pod_memory(pod)
                    }
                    for pod in pods.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Kubernetes API error: {e.reason}")
    
    def list_deployments(self, **kwargs) -> Dict[str, Any]:
        """List deployments"""
        namespace = kwargs.get("namespace", "default")
        
        try:
            deployments = self.apps.list_namespaced_deployment(namespace)
            
            return {
                "deployments": [
                    {
                        "name": dep.metadata.name,
                        "replicas": dep.spec.replicas,
                        "available": dep.status.available_replicas,
                        "created": dep.metadata.creation_timestamp.isoformat()
                    }
                    for dep in deployments.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Kubernetes API error: {e.reason}")
    
    def _get_node_cpu(self, node) -> str:
        try:
            allocatable = node.status.allocatable.get('cpu', '0')
            return f"{allocatable} cores"
        except:
            return "unknown"
    
    def _get_node_memory(self, node) -> str:
        try:
            allocatable = node.status.allocatable.get('memory', '0')
            return allocatable
        except:
            return "unknown"
    
    def _get_pod_cpu(self, pod) -> str:
        try:
            total_cpu = 0
            for container in pod.spec.containers:
                if container.resources and container.resources.requests:
                    cpu = container.resources.requests.get('cpu', '0')
                    if cpu.endswith('m'):
                        total_cpu += int(cpu[:-1]) / 1000
                    else:
                        total_cpu += float(cpu)
            return f"{total_cpu:.2f}"
        except:
            return "unknown"
    
    def _get_pod_memory(self, pod) -> str:
        try:
            for container in pod.spec.containers:
                if container.resources and container.resources.requests:
                    return container.resources.requests.get('memory', 'unknown')
            return "unknown"
        except:
            return "unknown"
