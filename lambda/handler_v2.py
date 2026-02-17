"""
CloudOps AI Gateway - Thin Lambda that delegates to real AI

KEY PRINCIPLE: This Lambda is a GATEWAY, not the intelligence.

What it does:
- Authenticates requests
- Delegates to AI providers (Gemini, OpenAI, etc.)
- Returns structured responses
- Logs for audit

What it does NOT do:
- Hard-code incident classification (uses real AI)
- Hard-code planning logic (returns strategy reference)
- Make security decisions (delegates to auth service)
"""
import json
import os
from datetime import datetime


def lambda_handler(event, context):
    """
    Thin gateway that delegates to AI providers
    """
    
    try:
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')
        user_context = body.get('context', {})
        
        if not query:
            return error_response(400, "Missing 'query' parameter")
        
        # Authenticate and get user context
        api_key = event.get('headers', {}).get('x-api-key', '')
        auth_result = validate_api_key(api_key, event)
        
        if not auth_result['valid']:
            return error_response(401, auth_result.get('error', 'Unauthorized'))
        
        # Add auth context
        user_context['user_id'] = auth_result['user_id']
        user_context['tenant_id'] = auth_result['tenant_id']
        
        # Delegate to REAL AI (not hard-coded)
        classification = classify_with_ai(query, user_context)
        
        # Return strategy reference (not hard-coded primitives)
        plan = {
            'plan_id': f"plan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'incident_class': classification['primary_class'],
            'note': 'Use client-side ReasoningPlanner to generate primitives'
        }
        
        # Log for audit
        log_request(auth_result['user_id'], query, classification)
        
        return success_response({
            'classification': classification,
            'plan': plan,
            'user_context': {
                'user_id': auth_result['user_id'],
                'tenant_id': auth_result['tenant_id']
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def classify_with_ai(query: str, context: dict) -> dict:
    """
    Delegate to REAL AI provider (not keyword matching)
    """
    
    ai_provider = os.environ.get('AI_PROVIDER', 'gemini')
    ai_api_key = os.environ.get('AI_API_KEY')
    
    if not ai_api_key:
        return fallback_classification(query)
    
    if ai_provider == 'gemini':
        return classify_with_gemini(query, ai_api_key)
    
    return fallback_classification(query)


def classify_with_gemini(query: str, api_key: str) -> dict:
    """Use Google Gemini for classification"""
    import urllib.request
    import urllib.parse
    
    prompt = f"""Classify this cloud incident into ONE class:
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

Return JSON: {{"primary_class": "...", "confidence": 0.0-1.0, "resource_type": "..."}}"""
    
    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
        data = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.0}
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        print(f"AI classification failed: {e}")
    
    return fallback_classification(query)


def fallback_classification(query: str) -> dict:
    """Minimal fallback when AI unavailable"""
    return {
        'primary_class': 'unknown',
        'confidence': 0.3,
        'resource_type': None,
        'query': query,
        'note': 'AI not configured - using fallback'
    }


def validate_api_key(api_key: str, event: dict) -> dict:
    """
    Validate API key and return user context
    
    TODO: Replace with proper auth:
    - DynamoDB lookup
    - JWT validation
    - IAM role assumption
    """
    
    if not api_key or not api_key.startswith('cloudops_'):
        return {'valid': False, 'error': 'Invalid API key format'}
    
    # TODO: Query DynamoDB for key metadata
    return {
        'valid': True,
        'user_id': 'demo_user',
        'tenant_id': 'demo_tenant',
        'permissions': ['investigate'],
        'note': 'Demo auth - implement proper auth for production'
    }


def log_request(user_id: str, query: str, classification: dict):
    """Log for audit"""
    print(json.dumps({
        'event': 'investigation',
        'user_id': user_id,
        'query': query,
        'class': classification['primary_class'],
        'timestamp': datetime.utcnow().isoformat()
    }))


def success_response(data: dict) -> dict:
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # TODO: Restrict in production
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key'
        },
        'body': json.dumps(data)
    }


def error_response(code: int, msg: str) -> dict:
    return {
        'statusCode': code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'error': msg,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
