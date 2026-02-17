#!/bin/bash

# CloudOps Phase 1 Deployment Script
# Deploys AI API to AWS Lambda + API Gateway in ap-south-1

set -e

echo "=================================="
echo "CloudOps Phase 1 Deployment"
echo "=================================="
echo ""

# Configuration
REGION="ap-south-1"
STACK_NAME="cloudops-ai-api"
TEMPLATE_FILE="cloudformation.yaml"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✓ AWS CLI configured"
echo ""

# Get AWS account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
echo ""

aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --region $REGION \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides ApiKeySecret=cloudops_$(date +%s) \
    --no-fail-on-empty-changeset

echo ""
echo "✓ Stack deployed successfully"
echo ""

# Get outputs
echo "Getting API endpoint..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
    --output text)

API_KEY=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`APIKey`].OutputValue' \
    --output text)

echo ""
echo "=================================="
echo "✓ DEPLOYMENT COMPLETE"
echo "=================================="
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo "API Key: $API_KEY"
echo ""
echo "Test your API:"
echo ""
echo "curl -X POST $API_ENDPOINT \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'x-api-key: $API_KEY' \\"
echo "  -d '{\"query\": \"high CPU on RDS\"}'"
echo ""
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Test the API with the curl command above"
echo "2. Configure CloudOps CLI: cloudops configure --api-endpoint $API_ENDPOINT --api-key $API_KEY"
echo "3. Run investigation: cloudops investigate 'high CPU on RDS'"
echo ""
