"""Provider factory for creating cloud and Kubernetes providers"""
from cloudops.providers import (
    CloudProvider, KubernetesProvider,
    AWSProvider, K8sProvider,
    MockCloudProvider, MockK8sProvider
)


def build_cloud_provider(config) -> CloudProvider:
    """Build cloud provider based on configuration"""
    
    # Check if real APIs should be used
    use_real = config.get("cloud.use_real_apis", False)
    
    if not use_real:
        return MockCloudProvider()
    
    # Determine provider type
    provider_type = config.get("cloud.primary", "aws")
    
    if provider_type == "aws":
        try:
            from cloudops.auth import AWSAuth
            
            # Use authenticated session if role_arn configured
            if config.get("cloud.aws.role_arn"):
                auth = AWSAuth(config)
                session = auth.get_session()
            else:
                import boto3
                session = boto3.Session()
            
            return AWSProvider(session)
        
        except Exception as e:
            print(f"Warning: Failed to initialize AWS provider: {e}")
            print("Falling back to mock provider")
            return MockCloudProvider()
    
    elif provider_type == "azure":
        # Placeholder for Phase 3
        raise NotImplementedError("Azure provider not implemented yet")
    
    elif provider_type == "gcp":
        # Placeholder for Phase 3
        raise NotImplementedError("GCP provider not implemented yet")
    
    else:
        raise ValueError(f"Unknown cloud provider: {provider_type}")


def build_kubernetes_provider(config) -> KubernetesProvider:
    """Build Kubernetes provider based on configuration"""
    
    # Check if real APIs should be used
    use_real = config.get("cloud.use_real_apis", False)
    
    if not use_real:
        return MockK8sProvider()
    
    try:
        return K8sProvider()
    except Exception as e:
        print(f"Warning: Failed to initialize Kubernetes provider: {e}")
        print("Falling back to mock provider")
        return MockK8sProvider()
