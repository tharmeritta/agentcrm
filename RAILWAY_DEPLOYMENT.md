# 🚀 SALES CRM DEPLOYMENT INSTRUCTIONS

## ✅ Prerequisites
- Railway account created at https://railway.app
- Railway CLI installed and logged in

## 📋 Deployment Steps

### Step 1: Login to Railway
```bash
railway login
```

### Step 2: Deploy Backend

1. **Create new project for backend:**
```bash
cd /app
railway init
# Choose: "Empty Project"
# Name: "sales-crm-backend"
```

2. **Set environment variables:**
```bash
railway variables set MONGO_URL="mongodb+srv://rangsimanrts:cawqin-9sinFy-dewbev@agentcrm.amshyrt.mongodb.net/?retryWrites=true&w=majority&appName=AgentCRM"
railway variables set JWT_SECRET_KEY="prod-secret-key-2025-sales-crm-system-secure-railway"
railway variables set DB_NAME="sales_crm_production"
```

3. **Deploy:**
```bash
railway up
```

4. **Generate domain:**
```bash
railway domain generate
```

5. **Get your backend URL:**
```bash
railway domain
# Copy this URL - you'll need it for frontend
```

### Step 3: Deploy Frontend

1. **Go to frontend directory:**
```bash
cd /app/frontend
```

2. **Update backend URL in .env.production:**
```bash
echo "REACT_APP_BACKEND_URL=https://YOUR_BACKEND_URL_HERE" > .env.production
```

3. **Build frontend:**
```bash
npm run build
```

4. **Create new Railway project for frontend:**
```bash
railway init
# Choose: "Empty Project"  
# Name: "sales-crm-frontend"
```

5. **Deploy frontend:**
```bash
railway up
```

6. **Generate domain:**
```bash
railway domain generate
```

## 🎉 Access Your Live CRM

Your Sales CRM System will be available at:
- **Frontend**: https://your-frontend-url.railway.app
- **Backend API**: https://your-backend-url.railway.app

### 🔑 Login Credentials
- **Super Admin**: tharme.ritta / Tharme@789

## 🔧 Troubleshooting

If deployment fails:

1. **Check logs:**
```bash
railway logs
```

2. **Redeploy:**
```bash
railway up --detach
```

3. **Check service status:**
```bash
railway status
```

## 🌐 Alternative: Use Automation Script

Run the automated deployment script:
```bash
./deploy-railway.sh
```

This will handle everything automatically!

---

## 📞 Support

If you encounter issues:
1. Check Railway dashboard: https://railway.app/dashboard
2. View deployment logs in Railway console
3. Ensure MongoDB Atlas connection string is correct
4. Verify environment variables are set properly