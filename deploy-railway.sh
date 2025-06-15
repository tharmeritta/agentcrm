#!/bin/bash

echo "🚀 SALES CRM DEPLOYMENT TO RAILWAY"
echo "==================================="
echo

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "Please install it from: https://railway.app/cli"
    exit 1
fi

echo "✅ Railway CLI found!"

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway!"
    echo "Please run: railway login"
    exit 1
fi

echo "✅ Railway login confirmed!"

echo
echo "📋 DEPLOYMENT STEPS:"
echo "1. Deploy Backend (FastAPI + MongoDB)"
echo "2. Deploy Frontend (React)"
echo "3. Configure environment variables"
echo "4. Test deployment"
echo

read -p "Ready to start deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo
echo "🔧 Step 1: Deploying Backend..."
echo "==============================="

# Create new Railway project for backend
railway init --name "sales-crm-backend"

# Set environment variables
echo "Setting environment variables..."
railway variables set MONGO_URL="mongodb+srv://rangsimanrts:cawqin-9sinFy-dewbev@agentcrm.amshyrt.mongodb.net/?retryWrites=true&w=majority&appName=AgentCRM"
railway variables set JWT_SECRET_KEY="prod-secret-key-2025-sales-crm-system-secure-railway"
railway variables set DB_NAME="sales_crm_production"
railway variables set NODE_ENV="production"

# Deploy backend
echo "Deploying backend..."
railway up --detach

echo "✅ Backend deployment initiated!"

# Get backend URL
BACKEND_URL=$(railway domain)
if [ -z "$BACKEND_URL" ]; then
    echo "Generating Railway domain..."
    railway domain generate
    BACKEND_URL=$(railway domain)
fi

echo "🌐 Backend URL: $BACKEND_URL"

echo
echo "🎨 Step 2: Deploying Frontend..."
echo "================================"

# Go to frontend directory
cd frontend

# Update frontend environment for production
echo "REACT_APP_BACKEND_URL=https://$BACKEND_URL" > .env.production

# Build frontend
echo "Building frontend..."
npm run build

# Create new Railway project for frontend
railway init --name "sales-crm-frontend"

# Deploy frontend
echo "Deploying frontend..."
railway up --detach

# Get frontend URL
FRONTEND_URL=$(railway domain)
if [ -z "$FRONTEND_URL" ]; then
    echo "Generating Railway domain..."
    railway domain generate
    FRONTEND_URL=$(railway domain)
fi

echo "✅ Frontend deployment initiated!"
echo "🌐 Frontend URL: https://$FRONTEND_URL"

echo
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo
echo "📱 Your Sales CRM System is now LIVE:"
echo "   Frontend: https://$FRONTEND_URL"
echo "   Backend:  https://$BACKEND_URL"
echo
echo "🔑 Super Admin Login:"
echo "   Username: tharme.ritta"
echo "   Password: Tharme@789"
echo
echo "⏰ Railway deployments may take 2-3 minutes to fully activate."
echo "💡 Check Railway dashboard for deployment status: https://railway.app/dashboard"
echo
echo "🎯 Next steps:"
echo "   1. Test the login at your frontend URL"
echo "   2. Create admin and agent accounts"
echo "   3. Start using your CRM system!"
echo
