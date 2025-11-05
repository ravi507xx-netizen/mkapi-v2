#!/bin/bash

echo "🚀 Universal AI API - Vercel Deployment Script"
echo "=============================================="
echo ""

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo "📦 Checking files..."

# Check if required files exist
if [[ ! -f "app_serverless.py" ]]; then
    echo "❌ app_serverless.py not found!"
    exit 1
fi

if [[ ! -f "vercel.json" ]]; then
    echo "❌ vercel.json not found!"
    exit 1
fi

if [[ ! -f "requirements.txt" ]]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo "✅ All required files found!"
echo ""

echo "🌐 Deploying to Vercel..."
vercel --prod

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Check your health endpoint: https://your-app.vercel.app/health"
echo "2. Get your default API key from the response"
echo "3. Test image generation: https://your-app.vercel.app/image?prompt=Taj%20Mahal&api_key=YOUR_KEY"
echo "4. Test ffinfo (requires credit): https://your-app.vercel.app/ffinfo?uid=123&api_key=YOUR_KEY"
echo ""
echo "📚 Full documentation: README.md"