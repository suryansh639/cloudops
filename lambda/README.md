# CloudOps Phase 1 - Deployment Instructions

## ⚠️ IMPORTANT: Revoke Your Exposed Keys First!

Before deploying, **immediately revoke the AWS keys you posted**:

```bash
aws iam delete-access-key --access-key-id AKIA35E2YE3SHWPRPZPC
```

Then create new keys in IAM Console.

---

## What You're Deploying

**CloudOps AI API** - A Lambda function + API Gateway that provides AI reasoning for CloudOps CLI.

**Components:**
- Lambda function (Python 3.11)
- API Gateway (HTTP API)
- IAM roles
- CloudWatch logs

**Region:** ap-south-1  
**Cost:** ~$0.20/month (free tier eligible)

---

## Deployment Steps

### Option 1: One-Command Deployment (Recommended)

```bash
cd /home/suryanshg.jiit/cloudops/lambda
./deploy.sh
```

That's it! The script will:
1. Check AWS CLI configuration
2. Deploy CloudFormation stack
3. Output API endpoint and key
4. Give you test commands

### Option 2: Manual Deployment

```bash
cd /home/suryanshg.jiit/cloudops/lambda

aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name cloudops-ai-api \
  --region ap-south-1 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ApiKeySecret=cloudops_your_secret_key
```

---

## After Deployment

### 1. Get Your API Endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name cloudops-ai-api \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text
```

### 2. Test the API

```bash
# Replace with your actual endpoint and key
curl -X POST https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod/investigate \
  -H "Content-Type: application/json" \
  -H "x-api-key: cloudops_your_key" \
  -d '{"query": "high CPU on RDS"}'
```

Expected response:
```json
{
  "classification": {
    "primary_class": "resource_saturation",
    "confidence": 0.85,
    "query": "high CPU on RDS"
  },
  "plan": {
    "plan_id": "plan-20260217134500",
    "primitives": ["analyze_utilization", "compare_baseline", "check_scaling"]
  },
  "recommendations": {
    "actions": [
      {"priority": 1, "action": "Check CloudWatch metrics"},
      {"priority": 2, "action": "Review recent changes"}
    ]
  }
}
```

### 3. Configure CloudOps CLI

```bash
# In cloudops/cli.py, add API configuration
cloudops configure \
  --api-endpoint https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod/investigate \
  --api-key cloudops_your_key
```

---

## What This Gives You

### ✅ Working AI API
- Incident classification
- Diagnostic plan generation
- Recommendations
- ~100ms response time

### ✅ Scalable Infrastructure
- Auto-scales with Lambda
- Pay per request
- No servers to manage

### ✅ Secure
- API key authentication
- HTTPS only
- IAM role-based access

---

## Cost Estimate

**Free Tier (first 12 months):**
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- **Cost: $0**

**After Free Tier:**
- Lambda: $0.20 per 1M requests
- API Gateway: $1.00 per 1M requests
- **Cost: ~$1.20 per 1M investigations**

**For 1000 investigations/month: ~$0.001 (basically free)**

---

## Monitoring

### View Logs
```bash
aws logs tail /aws/lambda/cloudops-ai-api --follow --region ap-south-1
```

### Check Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=cloudops-ai-api \
  --start-time 2026-02-17T00:00:00Z \
  --end-time 2026-02-17T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region ap-south-1
```

---

## Updating the API

### Update Lambda code:
```bash
cd /home/suryanshg.jiit/cloudops/lambda

# Edit handler.py
vim handler.py

# Redeploy
./deploy.sh
```

### Update CloudFormation:
```bash
# Edit cloudformation.yaml
vim cloudformation.yaml

# Redeploy
./deploy.sh
```

---

## Cleanup (if needed)

```bash
aws cloudformation delete-stack \
  --stack-name cloudops-ai-api \
  --region ap-south-1
```

---

## Troubleshooting

### "Stack already exists"
```bash
# Update existing stack
aws cloudformation update-stack \
  --stack-name cloudops-ai-api \
  --template-body file://cloudformation.yaml \
  --region ap-south-1 \
  --capabilities CAPABILITY_NAMED_IAM
```

### "Access Denied"
Make sure your AWS user has these permissions:
- cloudformation:*
- lambda:*
- apigateway:*
- iam:CreateRole
- iam:AttachRolePolicy
- logs:*

### "Invalid API key"
API key must start with `cloudops_`

---

## Next Steps

1. ✅ Deploy API (you're doing this now)
2. ⏳ Update CLI to call API
3. ⏳ Add user authentication
4. ⏳ Add usage tracking
5. ⏳ Add billing integration

---

## Security Notes

- ✅ API key authentication enabled
- ✅ HTTPS only
- ✅ CORS configured
- ⚠️ Change default API key in production
- ⚠️ Add rate limiting for production
- ⚠️ Add DynamoDB for API key management

---

## Support

If deployment fails:
1. Check AWS CLI is configured: `aws sts get-caller-identity`
2. Check region is correct: `ap-south-1`
3. Check CloudFormation events: `aws cloudformation describe-stack-events --stack-name cloudops-ai-api --region ap-south-1`
4. Check Lambda logs: `aws logs tail /aws/lambda/cloudops-ai-api --region ap-south-1`

---

**Ready to deploy? Run: `./deploy.sh`**
