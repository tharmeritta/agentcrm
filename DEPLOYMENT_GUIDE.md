# 🚀 SALES CRM DEPLOYMENT GUIDE

## 📋 Requirements Checklist
- ✅ MongoDB Atlas connection string provided
- ✅ Backend API ready (FastAPI + Python)
- ✅ Frontend ready (React)
- ✅ Railway CLI installed

## 🔧 Environment Variables Needed

### For Backend Deployment:
```
MONGO_URL=mongodb+srv://rangsimanrts:cawqin-9sinFy-dewbev@agentcrm.amshyrt.mongodb.net/?retryWrites=true&w=majority&appName=AgentCRM
JWT_SECRET_KEY=prod-secret-key-2025-sales-crm-system-secure-token
DB_NAME=sales_crm_production
PORT=8000
```

### For Frontend Deployment:
```
REACT_APP_BACKEND_URL=https://your-backend-url.railway.app
```

## 🚀 Deployment Steps

### Step 1: Deploy Backend
1. Login to Railway: `railway login`
2. Create new project: `railway init`
3. Set environment variables in Railway dashboard
4. Deploy: `railway up`

### Step 2: Deploy Frontend
1. Update frontend/.env with backend URL
2. Build frontend: `npm run build`
3. Deploy to Vercel/Netlify

## 🌐 Alternative Deployment Options

### Option A: Railway (Full Stack)
- Backend + Frontend in one platform
- Easy environment variable management
- Automatic SSL certificates

### Option B: Render.com
- Free tier for backend
- Static site hosting for frontend
- Great for production apps

### Option C: Vercel + Railway
- Vercel for frontend (global CDN)
- Railway for backend
- Best performance globally
