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
    Classify incident using REAL AI (not keyword matching)
    
    This Lambda is a GATEWAY, not the intelligence.
    Delegates to actual LLM for reasoning.
    """
    
    # Get AI provider from environment
    ai_provider = os.environ.get('AI_PROVIDER', 'gemini')
    ai_api_key = os.environ.get('AI_API_KEY')
    
    if not ai_api_key:
        # Fallback to simple classification only for demo
        return fallback_classification(query)
    
    # Call REAL AI
    if ai_provider == 'gemini':
        return classify_with_gemini(query, context, ai_api_key)
    elif ai_provider == 'openai':
        return classify_with_openai(query, context, ai_api_key)
    else:
        return fallback_classification(query)


def classify_with_gemini(query: str, context: dict, api_key: str) -> dict:
    """Use Google Gemini for classification"""
    import requests
    
    prompt = f"""Classify this cloud operations incident into ONE of these classes:
- resource_saturation
- load_spike
- configuration_drift
- dependency_failure
- scaling_failure
- network_connectivity
- permission_failure
- cost_anomaly
- deployment_regression
- availability_loss
- performance_degradation
- data_inconsistency

Query: "{query}"

Return JSON only:
{{"primary_class": "...", "confidence": 0.0-1.0, "resource_type": "...", "reasoning": "..."}}"""
    
    response = requests.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
        headers={'Content-Type': 'application/json'},
        params={'key': api_key},
        json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.0}
        },
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    
    return fallback_classification(query)


def fallback_classification(query: str) -> dict:
    """Fallback when AI is not available - minimal logic"""
    return {
        'primary_class': 'unknown',
        'confidence': 0.3,
        'resource_type': None,
        'query': query,
        'note': 'AI provider not configured - using fallback'
    }


def generate_plan(classification: dict) -> dict:
    """
    Generate diagnostic plan - delegates to reasoning planner
    
    This Lambda is a GATEWAY, not the planner.
    Returns strategy reference, not hard-coded primitives.
    """
    
    incident_class = classification['primary_class']
    
    # Return strategy reference, let client-side planner handle it
    # OR call a planning service (future enhancement)
    
    return {
        'plan_id': f"plan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        'incident_class': incident_class,
        'strategy': incident_class,  # Reference to strategy, not primitives
        'note': 'Client should use ReasoningPlanner to generate primitives'
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


def validate_api_key(api_key: str, event: dict) -> dict:
    """
    Validate API key and return user context
    
    Returns: {'valid': bool, 'user_id': str, 'tenant_id': str, 'permissions': []}
    
    TODO: Replace with proper auth:
    - DynamoDB lookup for API keys
    - JWT token validation
    - IAM role assumption
    - OAuth2/OIDC integration
    """
    
    # Get valid API keys from environment (temporary)
    valid_keys = os.environ.get('VALID_API_KEYS', '').split(',')
    
    # Basic validation
    if not api_key or not api_key.startswith('cloudops_'):
        return {'valid': False, 'error': 'Invalid API key format'}
    
    # TODO: Query DynamoDB for key metadata
    # key_data = dynamodb.get_item(Key={'api_key': api_key})
    
    # For now, accept any key with correct prefix
    if api_key in valid_keys or api_key.startswith('cloudops_'):
        return {
            'valid': True,
            'user_id': 'demo_user',
            'tenant_id': 'demo_tenant',
            'permissions': ['investigate', 'read'],
            'note': 'Using demo auth - implement proper auth for production'
        }
    
    return {'valid': False, 'error': 'API key not found'}


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
