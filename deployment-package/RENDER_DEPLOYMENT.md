# 🚀 RENDER.COM DEPLOYMENT GUIDE - SALES CRM

## ✅ Prerequisites
- GitHub account
- Render.com account (free)

## 📁 Repository Setup

### Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `sales-crm-system`
3. Make it Public
4. Click "Create repository"

### Step 2: Upload Your Code

**Option A: Upload via GitHub Web Interface**
1. Click "uploading an existing file"
2. Drag and drop all files from `/app/` directory
3. Commit files

**Option B: Use Git Commands (if available)**
```bash
git init
git add .
git commit -m "Initial commit - Sales CRM System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sales-crm-system.git
git push -u origin main
```

## 🔧 Step 3: Deploy Backend on Render

1. **Go to**: https://render.com
2. **Sign up/Login** with GitHub
3. **Click**: "New" → "Web Service"
4. **Connect GitHub** → Select `sales-crm-system` repo
5. **Configure**:
   - **Name**: `sales-crm-backend`
   - **Region**: Oregon (US West) or Frankfurt (Europe)
   - **Branch**: `main`
   - **Root Directory**: Leave empty (uses root)
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

6. **Environment Variables** (click "Advanced"):
   ```
   MONGO_URL=mongodb+srv://rangsimanrts:cawqin-9sinFy-dewbev@agentcrm.amshyrt.mongodb.net/?retryWrites=true&w=majority&appName=AgentCRM
   JWT_SECRET_KEY=prod-secret-key-2025-sales-crm-system-secure-render
   DB_NAME=sales_crm_production
   PYTHON_VERSION=3.11.0
   ```

7. **Click**: "Create Web Service"

## 🎨 Step 4: Deploy Frontend on Render

1. **Click**: "New" → "Static Site"
2. **Connect GitHub** → Select `sales-crm-system` repo
3. **Configure**:
   - **Name**: `sales-crm-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`

4. **Environment Variables**:
   ```
   REACT_APP_BACKEND_URL=https://sales-crm-backend.onrender.com
   ```
   *(Replace with your actual backend URL from step 3)*

5. **Click**: "Create Static Site"

## 🎉 Step 5: Access Your Live CRM

After deployment (5-10 minutes), your URLs will be:
- **Frontend**: `https://sales-crm-frontend.onrender.com`
- **Backend**: `https://sales-crm-backend.onrender.com`

### 🔑 Login Credentials
- **Super Admin**: `tharme.ritta` / `Tharme@789`

## 🔧 Important Notes

1. **Free Tier Limitations**:
   - Services sleep after 15 minutes of inactivity
   - First request may take 30-60 seconds to wake up
   - 750 hours/month free usage

2. **Update Frontend URL**:
   After backend deploys, update frontend environment variable with actual backend URL

3. **Custom Domains** (Optional):
   - Available on paid plans
   - Can use your own domain names

## 🚨 Troubleshooting

**If backend fails to deploy**:
1. Check Render logs for errors
2. Verify all environment variables are set
3. Ensure MongoDB connection string is correct

**If frontend fails to deploy**:
1. Check build logs
2. Verify `REACT_APP_BACKEND_URL` points to correct backend
3. Ensure all dependencies are in package.json

## 📞 Need Help?

- Render Documentation: https://render.com/docs
- Check service logs in Render dashboard
- Ensure GitHub repo has all necessary files

---

**Once deployed, your Sales CRM will be accessible worldwide! 🌍**