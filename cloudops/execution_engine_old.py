"""Execution engine for running plans"""
import uuid
import time
from typing import List
from pydantic import BaseModel
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from kubernetes import client, config as k8s_config
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class StepResult(BaseModel):
    step_id: int
    status: str
    started_at: str
    completed_at: str
    output: dict
    error: str = None


class Execution(BaseModel):
    execution_id: str
    plan_id: str
    status: str
    steps: List[StepResult]


class ExecutionEngine:
    def __init__(self, config):
        self.config = config
        self.use_real_aws = BOTO3_AVAILABLE and config.get("cloud.use_real_apis", False)
        self.use_real_k8s = K8S_AVAILABLE and config.get("cloud.use_real_apis", False)
        
        if self.use_real_aws:
            self._init_aws()
        if self.use_real_k8s:
            self._init_k8s()
    
    def _init_aws(self):
        """Initialize AWS clients"""
        try:
            from cloudops.auth import AWSAuth
            
            # Use authenticated session if role_arn configured
            if self.config.get("cloud.aws.role_arn"):
                auth = AWSAuth(self.config)
                session = auth.get_session()
            else:
                session = boto3.Session()
            
            self.ec2 = session.client('ec2')
            self.cloudwatch = session.client('cloudwatch')
            self.ce = session.client('ce')
            self.config_service = session.client('config')
        except Exception as e:
            print(f"Warning: Failed to initialize AWS clients: {e}")
            self.use_real_aws = False
    
    def _init_k8s(self):
        """Initialize Kubernetes client"""
        try:
            k8s_config.load_kube_config()
            self.k8s_core = client.CoreV1Api()
            self.k8s_apps = client.AppsV1Api()
        except Exception as e:
            print(f"Warning: Failed to initialize K8s client: {e}")
            self.use_real_k8s = False
    
    def execute(self, plan) -> Execution:
        """Execute a plan"""
        execution = Execution(
            execution_id=str(uuid.uuid4()),
            plan_id=plan.plan_id,
            status="running",
            steps=[]
        )
        
        for step in plan.steps:
            result = self._execute_step(step)
            execution.steps.append(result)
            
            if result.status == "failed":
                execution.status = "failed"
                break
        
        if execution.status != "failed":
            execution.status = "completed"
        
        return execution
    
    def _execute_step(self, step) -> StepResult:
        """Execute a single step"""
        started_at = datetime.utcnow().isoformat() + "Z"
        
        try:
            # Route to appropriate executor
            if step.provider == "kubernetes":
                output = self._execute_kubernetes(step)
            elif step.provider == "aws":
                output = self._execute_aws(step)
            elif step.provider == "local":
                output = self._execute_local(step)
            else:
                raise ValueError(f"Unknown provider: {step.provider}")
            
            # Simulate execution time
            time.sleep(1)
            
            completed_at = datetime.utcnow().isoformat() + "Z"
            
            return StepResult(
                step_id=step.step_id,
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                output=output
            )
        
        except Exception as e:
            completed_at = datetime.utcnow().isoformat() + "Z"
            return StepResult(
                step_id=step.step_id,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                output={},
                error=str(e)
            )
    
    def _execute_kubernetes(self, step) -> dict:
        """Execute Kubernetes operations"""
        if not self.use_real_k8s:
            return self._execute_kubernetes_mock(step)
        
        try:
            if step.method == "list_nodes":
                nodes = self.k8s_core.list_node()
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
            
            elif step.method == "top_pods":
                namespace = step.params.get("namespace", "default")
                all_ns = step.params.get("all_namespaces", False)
                
                if all_ns:
                    pods = self.k8s_core.list_pod_for_all_namespaces()
                else:
                    pods = self.k8s_core.list_namespaced_pod(namespace)
                
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
            
            elif step.method == "list_deployments":
                namespace = step.params.get("namespace", "default")
                deployments = self.k8s_apps.list_namespaced_deployment(namespace)
                
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
            
            return {"status": "success"}
        
        except ApiException as e:
            raise Exception(f"Kubernetes API error: {e.reason}")
    
    def _execute_kubernetes_mock(self, step) -> dict:
        """Mock Kubernetes execution"""
        if step.method == "list_nodes":
            return {
                "nodes": [
                    {"name": "node-1", "cpu": "95%", "memory": "70%"},
                    {"name": "node-2", "cpu": "45%", "memory": "60%"},
                    {"name": "node-3", "cpu": "50%", "memory": "55%"}
                ]
            }
        elif step.method == "top_pods":
            return {
                "pods": [
                    {"name": "api-gateway-7d8f9", "namespace": "prod", "cpu": "3.2", "memory": "2.1Gi"},
                    {"name": "worker-abc123", "namespace": "prod", "cpu": "1.5", "memory": "1.8Gi"}
                ]
            }
        elif step.method == "list_deployments":
            return {
                "deployments": [
                    {"name": "api-gateway", "version": "v2.3.1", "deployed_at": "2026-02-17T09:00:00Z"}
                ]
            }
        return {"status": "success"}
    
    def _execute_aws(self, step) -> dict:
        """Execute AWS operations"""
        if not self.use_real_aws:
            return self._execute_aws_mock(step)
        
        try:
            if step.method == "cloudwatch_get_metrics":
                metric = step.params.get("metric", "CPUUtilization")
                period = step.params.get("period", 3600)
                stat = step.params.get("stat", "Average")
                
                from datetime import timedelta
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(seconds=period)
                
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
            
            elif step.method == "cost_explorer_get_cost":
                time_period = step.params.get("time_period", "LAST_30_DAYS")
                granularity = step.params.get("granularity", "DAILY")
                
                from datetime import timedelta
                end = datetime.utcnow().date()
                start = end - timedelta(days=30)
                
                response = self.ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start.isoformat(),
                        'End': end.isoformat()
                    },
                    Granularity=granularity,
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
            
            elif step.method == "ec2_describe_security_groups":
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
            
            return {"status": "success"}
        
        except (ClientError, BotoCoreError) as e:
            raise Exception(f"AWS API error: {str(e)}")
    
    def _execute_aws_mock(self, step) -> dict:
        """Mock AWS execution"""
        if step.method == "cloudwatch_get_metrics":
            return {
                "datapoints": [
                    {"timestamp": "2026-02-17T10:00:00Z", "average": 92.3},
                    {"timestamp": "2026-02-17T09:00:00Z", "average": 45.0}
                ]
            }
        elif step.method == "cost_explorer_get_cost":
            return {
                "total": 1250.45,
                "by_service": {
                    "EC2": 650.20,
                    "RDS": 300.15,
                    "S3": 200.10,
                    "Other": 100.00
                }
            }
        elif step.method == "ec2_describe_security_groups":
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
        return {"status": "success"}
    
    def _execute_local(self, step) -> dict:
        """Execute local analysis"""
        if step.method == "analyze_security_rules":
            return {
                "risky_groups": [
                    {
                        "id": "sg-12345",
                        "name": "web-servers",
                        "risk": "high",
                        "reason": "Allows unrestricted access from 0.0.0.0/0"
                    }
                ]
            }
        
        return {"status": "success"}
    
    def _get_node_cpu(self, node) -> str:
        """Extract CPU usage from node"""
        try:
            allocatable = node.status.allocatable.get('cpu', '0')
            return f"{allocatable} cores"
        except:
            return "unknown"
    
    def _get_node_memory(self, node) -> str:
        """Extract memory usage from node"""
        try:
            allocatable = node.status.allocatable.get('memory', '0')
            return allocatable
        except:
            return "unknown"
    
    def _get_pod_cpu(self, pod) -> str:
        """Extract CPU request from pod"""
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
        """Extract memory request from pod"""
        try:
            for container in pod.spec.containers:
                if container.resources and container.resources.requests:
                    return container.resources.requests.get('memory', 'unknown')
            return "unknown"
        except:
            return "unknown"
