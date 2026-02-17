"""
CloudOps AI API - Lambda Handler

This Lambda function provides the AI reasoning endpoint for CloudOps CLI.
Customers call this API to get incident classification and recommendations.
"""
import json
import os
from datetime import datetime


def lambda_handler(event, context):
    """
    Main Lambda handler for CloudOps AI API
    
    Endpoint: POST /investigate
    Body: {"query": "high CPU on RDS", "context": {...}}
    """
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')
        user_context = body.get('context', {})
        
        if not query:
            return error_response(400, "Missing 'query' parameter")
        
        # Get API key from header
        api_key = event.get('headers', {}).get('x-api-key', '')
        
        # Validate API key (simple validation for now)
        if not validate_api_key(api_key):
            return error_response(401, "Invalid API key")
        
        # Classify incident using AI
        classification = classify_incident(query, user_context)
        
        # Generate diagnostic plan
        plan = generate_plan(classification)
        
        # Generate recommendations
        recommendations = generate_recommendations(classification, plan)
        
        # Return response
        return success_response({
            'classification': classification,
            'plan': plan,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, f"Internal error: {str(e)}")


def classify_incident(query: str, context: dict) -> dict:
    """
    Classify incident using AI (simplified for Phase 1)
    
    In production, this would call OpenAI/Anthropic/Gemini API
    For now, using simple pattern matching
    """
    
    query_lower = query.lower()
    
    # Simple classification logic
    if any(word in query_lower for word in ['cpu', 'memory', 'disk', 'high']):
        primary_class = 'resource_saturation'
        confidence = 0.85
    elif any(word in query_lower for word in ['slow', 'latency', 'timeout']):
        primary_class = 'performance_degradation'
        confidence = 0.80
    elif any(word in query_lower for word in ['down', 'unavailable', 'crash']):
        primary_class = 'availability_loss'
        confidence = 0.90
    elif any(word in query_lower for word in ['deploy', 'release', 'version']):
        primary_class = 'deployment_regression'
        confidence = 0.75
    else:
        primary_class = 'unknown'
        confidence = 0.50
    
    # Extract resource type
    resource_type = None
    if 'rds' in query_lower or 'database' in query_lower:
        resource_type = 'rds'
    elif 'ec2' in query_lower or 'instance' in query_lower:
        resource_type = 'ec2'
    elif 'lambda' in query_lower:
        resource_type = 'lambda'
    elif 'pod' in query_lower or 'kubernetes' in query_lower:
        resource_type = 'pod'
    
    return {
        'primary_class': primary_class,
        'confidence': confidence,
        'resource_type': resource_type,
        'query': query
    }


def generate_plan(classification: dict) -> dict:
    """
    Generate diagnostic plan based on incident class
    """
    
    incident_class = classification['primary_class']
    
    # Map incident class to primitives
    strategies = {
        'resource_saturation': [
            'analyze_utilization',
            'compare_baseline',
            'find_top_consumers',
            'check_scaling_behavior',
            'check_recent_changes'
        ],
        'performance_degradation': [
            'analyze_latency',
            'compare_baseline',
            'trace_dependencies',
            'check_recent_changes'
        ],
        'availability_loss': [
            'check_resource_status',
            'check_health_checks',
            'trace_dependencies',
            'check_recent_changes'
        ],
        'deployment_regression': [
            'check_deployment_status',
            'compare_versions',
            'analyze_error_rate',
            'check_recent_changes'
        ]
    }
    
    primitives = strategies.get(incident_class, ['analyze_utilization', 'check_recent_changes'])
    
    return {
        'plan_id': f"plan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        'incident_class': incident_class,
        'primitives': primitives,
        'estimated_duration_seconds': len(primitives) * 3
    }


def generate_recommendations(classification: dict, plan: dict) -> dict:
    """
    Generate recommendations based on classification
    """
    
    incident_class = classification['primary_class']
    resource_type = classification.get('resource_type', 'unknown')
    
    # Generate recommendations based on incident type
    recommendations = {
        'resource_saturation': {
            'actions': [
                {
                    'priority': 1,
                    'action': f'Check {resource_type} metrics in CloudWatch',
                    'command': f'aws cloudwatch get-metric-statistics --namespace AWS/{resource_type.upper()}'
                },
                {
                    'priority': 2,
                    'action': 'Check for recent configuration changes',
                    'command': 'aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceType'
                },
                {
                    'priority': 3,
                    'action': 'Review auto-scaling configuration',
                    'command': 'aws autoscaling describe-auto-scaling-groups'
                }
            ]
        },
        'performance_degradation': {
            'actions': [
                {
                    'priority': 1,
                    'action': 'Check latency metrics',
                    'command': 'aws cloudwatch get-metric-statistics --metric-name Latency'
                },
                {
                    'priority': 2,
                    'action': 'Check for recent deployments',
                    'command': 'aws deploy list-deployments'
                }
            ]
        },
        'availability_loss': {
            'actions': [
                {
                    'priority': 1,
                    'action': f'Check {resource_type} status',
                    'command': f'aws {resource_type} describe-instances' if resource_type == 'ec2' else 'aws ecs describe-services'
                },
                {
                    'priority': 2,
                    'action': 'Check health checks',
                    'command': 'aws elbv2 describe-target-health'
                }
            ]
        }
    }
    
    default_actions = [
        {
            'priority': 1,
            'action': 'Review CloudWatch metrics',
            'command': 'aws cloudwatch list-metrics'
        }
    ]
    
    return recommendations.get(incident_class, {'actions': default_actions})


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key
    
    For Phase 1, using simple validation.
    In production, check against DynamoDB table.
    """
    
    # Get valid API keys from environment variable
    valid_keys = os.environ.get('VALID_API_KEYS', '').split(',')
    
    # For demo, accept any key that starts with 'cloudops_'
    if api_key.startswith('cloudops_'):
        return True
    
    return api_key in valid_keys


def success_response(data: dict) -> dict:
    """Return success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> dict:
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
