#!/bin/bash

echo "🚀 Starting Universal AI API Server..."
echo "📋 Available endpoints after startup:"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • ReDoc: http://localhost:8000/redoc"
echo "   • Health: http://localhost:8000/health"
echo ""
echo "🔧 Starting server..."

# Start the FastAPI server
uvicorn user_input_files.mkapi_v1:app --host 0.0.0.0 --port 8000 --reload