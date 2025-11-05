# Universal AI API - Vercel Deployment Guide

## 📋 **Files Created:**

1. **`vercel.json`** - Main configuration with full features
2. **`vercel_simple.json`** - Simplified configuration  
3. **`app_serverless.py`** - Serverless-compatible FastAPI app

## 🚀 **Quick Deployment to Vercel**

### **Step 1: Install Vercel CLI**
```bash
npm install -g vercel
```

### **Step 2: Deploy**
```bash
vercel --prod
```

### **Step 3: Set Environment Variables (Optional)**
```bash
vercel env add PYTHON_VERSION
# Enter: 3.9

vercel env add PORT
# Enter: 8000
```

## 📁 **File Structure**
```
your-project/
├── app_serverless.py     # Main FastAPI application
├── vercel.json          # Vercel configuration (full features)
├── vercel_simple.json   # Vercel configuration (basic)
├── requirements.txt     # Python dependencies
└── vercel.json          # (Copy from either config)
```

## 🔧 **Configuration Options**

### **Option 1: Full Featured (Recommended)**
Use `vercel.json` with these features:
- ✅ CORS headers for API access
- ✅ Security headers
- ✅ Health check cron job
- ✅ Python 3.9 runtime
- ✅ 60-second timeout

### **Option 2: Basic Setup**
Use `vercel_simple.json` for minimal configuration:
- ✅ Python 3.9 runtime
- ✅ Basic routing
- ✅ No additional headers

## 🌐 **API Endpoints After Deployment**

Your API will be available at: `https://your-app.vercel.app`

### **Free Endpoints (0 credits)**
- `GET /image?prompt=Taj%20Mahal&api_key=YOUR_KEY` - Direct image URL
- `GET /text?prompt=Hello&api_key=YOUR_KEY` - AI text response
- `GET /qr?text=Hello&api_key=YOUR_KEY` - Direct QR code URL
- `GET /voice?text=Hello&api_key=YOUR_KEY` - Direct audio URL

### **Paid Endpoints**
- `GET /ffinfo?uid=123&api_key=YOUR_KEY` - Redirect (1 credit) - **NEW: Now uses MK_DEVELOPER**
- `GET /video?prompt=Hello&api_key=YOUR_KEY` - Video generation (2 credits)
- `GET /num?mobile=123&api_key=YOUR_KEY` - Number service (5 credits)

### **Admin Endpoints**
- `GET /admin/generateapi?admin_username=mk&admin_password=mk123` - Create API keys
- `GET /admin/listapi?admin_username=mk&admin_password=mk123` - List all API keys
- `GET /admin/addcredits?admin_username=mk&admin_password=mk123&api_key=KEY&credits_to_add=10` - Add credits

### **Utility Endpoints**
- `GET /api_key?api_key=YOUR_KEY` - Check your API key usage
- `GET /health` - Health check status

## 🔑 **Getting Your First API Key**

After deployment, get the default test API key:

1. Visit: `https://your-app.vercel.app/health`
2. Look for the default API key in the response
3. Or generate one using admin endpoint:
   ```
   GET /admin/generateapi?admin_username=mk&admin_password=mk123
   ```

## 📊 **Response Format Examples**

### **Image Generation (Direct URL)**
```http
GET https://your-app.vercel.app/image?prompt=Taj%20Mahal&api_key=YOUR_KEY
```
**Response**: `https://image.pollinations.ai/prompt/Taj%20Mahal?width=512&height=512&nologo=true`

### **FFInfo (Credit Required)**
```http
GET https://your-app.vercel.app/ffinfo?uid=12345&api_key=YOUR_KEY
```
**Response**: Redirect to `https://danger-info-alpha.vercel.app/accinfo?uid=12345&key=MK_DEVELOPER`
**Cost**: 1 credit

### **QR Code (Direct URL)**
```http
GET https://your-app.vercel.app/qr?text=Hello%20World&api_key=YOUR_KEY
```
**Response**: Direct QR code image URL

## 🛠️ **Testing Your Deployment**

### **1. Health Check**
```bash
curl https://your-app.vercel.app/health
```

### **2. Test Image Generation**
```bash
curl "https://your-app.vercel.app/image?prompt=Beautiful%20sunset&api_key=YOUR_API_KEY"
```

### **3. Test FFInfo (with credit)**
```bash
curl -L "https://your-app.vercel.app/ffinfo?uid=12345&api_key=YOUR_API_KEY"
```

## 🔄 **Update Your Application**

To update your API:

1. **Modify `app_serverless.py`** with your changes
2. **Redeploy:**
   ```bash
   vercel --prod
   ```

## 🐛 **Troubleshooting**

### **500 Internal Server Error**
- Ensure you're using `app_serverless.py` (not the SQLite version)
- Check the health endpoint for error details
- Verify all dependencies are in `requirements.txt`

### **Function Timeout**
- Increase `maxDuration` in vercel.json if needed
- Consider external API timeouts

### **Memory Issues**
- The app_serverless.py includes automatic cleanup
- Monitor memory usage in Vercel dashboard

## 📈 **Performance Tips**

1. **Use CDN**: Vercel automatically provides global CDN
2. **Keep-alive**: Connections are automatically optimized
3. **Caching**: Headers are configured for optimal caching
4. **Regions**: Deployed in iad1 (Virginia) by default

## 🔒 **Security Features**

- ✅ CORS headers configured
- ✅ Security headers (XSS, Content-Type, Frame Options)
- ✅ API key authentication
- ✅ Credit system prevents abuse
- ✅ Request logging for monitoring

Your Universal AI API is now ready for production deployment! 🎉