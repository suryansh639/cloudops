# Provider Architecture

## Overview

CloudOps uses a **provider abstraction layer** to decouple the execution engine from specific cloud implementations. This enables:

- Clean separation of concerns
- Easy testing (swap real providers with mocks)
- Multi-cloud support without modifying core engine
- Customer-hosted mode support

## Architecture

```
ExecutionEngine (provider-agnostic)
        ↓
ProviderFactory (decides which provider)
        ↓
Provider Interface (abstract)
        ↓
    ┌───┴───┬───────┬──────┐
    ↓       ↓       ↓      ↓
  AWS    Azure   GCP   Mock
```

## Key Principle

**ExecutionEngine must NOT know about AWS, Kubernetes, Azure, or GCP directly.**

Instead, it depends on abstract interfaces that are implemented by concrete providers.

## Provider Interfaces

### CloudProvider

```python
class CloudProvider(ABC):
    @abstractmethod
    def get_cpu_metrics(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_cost_data(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def list_security_groups(self, **kwargs) -> Dict[str, Any]:
        pass
```

### KubernetesProvider

```python
class KubernetesProvider(ABC):
    @abstractmethod
    def list_nodes(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def list_pods(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def list_deployments(self, **kwargs) -> Dict[str, Any]:
        pass
```

## Implementations

### Real Providers

**AWSProvider** (`providers/aws.py`)
- Uses boto3 SDK
- Handles AWS authentication
- Implements CloudProvider interface

**K8sProvider** (`providers/kubernetes.py`)
- Uses kubernetes client
- Handles kubeconfig
- Implements KubernetesProvider interface

### Mock Providers

**MockCloudProvider** (`providers/mock.py`)
- Returns fake data
- No external dependencies
- Used for testing and demos

**MockK8sProvider** (`providers/mock.py`)
- Returns fake Kubernetes data
- No cluster required
- Used for testing and demos

## Provider Factory

The factory decides which provider to use based on configuration:

```python
def build_cloud_provider(config) -> CloudProvider:
    use_real = config.get("cloud.use_real_apis", False)
    
    if not use_real:
        return MockCloudProvider()
    
    provider_type = config.get("cloud.primary", "aws")
    
    if provider_type == "aws":
        return AWSProvider(session)
    elif provider_type == "azure":
        return AzureProvider(credentials)
    # ...
```

## Execution Engine

The engine is now **provider-agnostic**:

```python
class ExecutionEngine:
    def __init__(self, config, cloud_provider=None, k8s_provider=None):
        self.cloud = cloud_provider or build_cloud_provider(config)
        self.k8s = k8s_provider or build_kubernetes_provider(config)
    
    def _execute_cloud(self, step):
        # Doesn't know if it's AWS, Azure, or mock
        return self.cloud.get_cpu_metrics(**step.params)
```

## Benefits

### 1. Testability

```python
# Unit test with mock provider
mock_cloud = MockCloudProvider()
engine = ExecutionEngine(config, cloud_provider=mock_cloud)
```

### 2. Multi-Cloud

```python
# Switch providers without changing engine
if config.cloud == "aws":
    provider = AWSProvider(session)
elif config.cloud == "azure":
    provider = AzureProvider(credentials)

engine = ExecutionEngine(config, cloud_provider=provider)
```

### 3. Customer-Hosted

```python
# Customer implements their own provider
class CustomProvider(CloudProvider):
    def get_cpu_metrics(self, **kwargs):
        # Custom implementation
        pass

engine = ExecutionEngine(config, cloud_provider=CustomProvider())
```

### 4. Gradual Migration

```python
# Can disable AWS without breaking engine
config.set("cloud.use_real_apis", False)
# Engine automatically uses mock provider
```

## Configuration

### Enable Real APIs

```yaml
cloud:
  use_real_apis: true
  primary: aws
```

### Use Mock Providers

```yaml
cloud:
  use_real_apis: false
```

### Provider-Specific Config

```yaml
cloud:
  primary: aws
  aws:
    role_arn: arn:aws:iam::123456789012:role/CloudOpsRole
    session_duration: 3600
```

## Adding New Providers

### Step 1: Implement Interface

```python
# providers/azure.py
class AzureProvider(CloudProvider):
    def __init__(self, credentials):
        self.client = AzureClient(credentials)
    
    def get_cpu_metrics(self, **kwargs):
        return self.client.get_metrics(...)
```

### Step 2: Update Factory

```python
# providers/factory.py
def build_cloud_provider(config):
    # ...
    elif provider_type == "azure":
        return AzureProvider(credentials)
```

### Step 3: Done

No changes needed to:
- ExecutionEngine
- PlanningEngine
- CLI
- Tests

## Testing Strategy

### Unit Tests

```python
def test_execution_with_mock():
    mock_cloud = MockCloudProvider()
    engine = ExecutionEngine(config, cloud_provider=mock_cloud)
    # Test without AWS credentials
```

### Integration Tests

```python
def test_execution_with_real_aws():
    real_cloud = AWSProvider(session)
    engine = ExecutionEngine(config, cloud_provider=real_cloud)
    # Test with real AWS
```

### Provider Tests

```python
def test_aws_provider():
    provider = AWSProvider(session)
    result = provider.get_cpu_metrics()
    assert "datapoints" in result
```

## Migration from Old Code

### Before (Tight Coupling)

```python
class ExecutionEngine:
    def __init__(self, config):
        self.ec2 = boto3.client('ec2')  # ❌ Hardcoded AWS
        self.cloudwatch = boto3.client('cloudwatch')
```

### After (Loose Coupling)

```python
class ExecutionEngine:
    def __init__(self, config, cloud_provider=None):
        self.cloud = cloud_provider or build_cloud_provider(config)  # ✅ Abstracted
```

## File Structure

```
cloudops/providers/
├── __init__.py           # Package exports
├── base.py               # Abstract interfaces
├── aws.py                # AWS implementation
├── kubernetes.py         # Kubernetes implementation
├── mock.py               # Mock implementations
└── factory.py            # Provider factory
```

## Best Practices

### DO ✅

- Depend on interfaces, not implementations
- Use factory to create providers
- Keep providers stateless where possible
- Handle errors in providers, not engine
- Return consistent data structures

### DON'T ❌

- Import boto3/kubernetes in ExecutionEngine
- Check provider type in engine (`if aws...`)
- Mix provider logic with execution logic
- Hardcode provider-specific behavior
- Leak provider details to upper layers

## Future Extensions

### Phase 3: Multi-Cloud

- Add AzureProvider
- Add GCPProvider
- Multi-cloud playbooks

### Phase 4: Custom Providers

- Plugin system for custom providers
- Provider marketplace
- Community providers

### Phase 5: Advanced Features

- Provider health checks
- Automatic failover
- Provider metrics
- Cost optimization across providers

## Comparison with Industry Standards

This pattern is used by:

- **Terraform**: Provider plugins
- **Pulumi**: Resource providers
- **Crossplane**: Composition providers
- **Kubernetes**: Cloud provider interface

CloudOps follows the same proven architecture.
