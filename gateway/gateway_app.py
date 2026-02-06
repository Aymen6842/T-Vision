from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import uvicorn

app = FastAPI(title="Vision AI API Gateway")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "captioning": "http://localhost:8001",
    "masking": "http://localhost:8002",
    "chatbot": "http://localhost:8003",
    "ocr": "http://localhost:8004",
}

@app.get("/")
async def root():
    return {
        "message": "Vision AI API Gateway",
        "version": "1.0.0",
        "services": list(SERVICES.keys())
    }

@app.get("/health")
async def health_check():
    """Aggregate health check for all services"""
    health_status = {
        "gateway": "healthy",
        "services": {}
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                # Try /health endpoint first, fallback to /
                try:
                    response = await client.get(f"{service_url}/health")
                except httpx.HTTPStatusError:
                    response = await client.get(f"{service_url}/")
                
                health_status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url
                }
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "url": service_url
                }
    
    # Gateway is unhealthy if any critical service is down
    critical_services = ["chatbot"]
    if any(health_status["services"].get(svc, {}).get("status") != "healthy" 
           for svc in critical_services):
        health_status["gateway"] = "degraded"
    
    return health_status

async def proxy_request(service_url: str, request: Request, path: str):
    """Generic proxy function to forward requests to microservices"""
    # Build target URL
    target_url = f"{service_url}/{path}"
    
    # Get request body and headers
    body = await request.body()
    headers = dict(request.headers)
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
                params=request.query_params
            )
            
            # Handle streaming responses (for images)
            if response.headers.get("content-type", "").startswith("image/"):
                return StreamingResponse(
                    response.iter_bytes(),
                    media_type=response.headers.get("content-type"),
                    status_code=response.status_code
                )
            
            # Handle JSON responses
            return JSONResponse(
                content=response.json() if response.text else {},
                status_code=response.status_code
            )
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"Service timeout: {service_url}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

# Route: Chatbot Service
@app.api_route("/api/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def chatbot_proxy(path: str, request: Request):
    # Add /chat prefix since chatbot expects /chat/start not just /start
    # Add /chat prefix since chatbot expects /chat/start not just /start
    return await proxy_request(SERVICES["chatbot"], request, f"chat/{path}")

# Route: Auth
@app.api_route("/auth/{path:path}", methods=["GET", "POST"])
async def auth_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["chatbot"], request, f"auth/{path}")


# Route: Captioning Service
@app.api_route("/api/caption/{path:path}", methods=["GET", "POST"])
async def caption_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["captioning"], request, path)

# Route: OCR Service
@app.api_route("/api/ocr/{path:path}", methods=["GET", "POST"])
async def ocr_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["ocr"], request, path)

# Route: Masking Service
@app.api_route("/api/masking/{path:path}", methods=["GET", "POST"])
async def masking_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["masking"], request, path)

if __name__ == "__main__":
    print("Starting API Gateway on port 8000...")
    print("Services:")
    for name, url in SERVICES.items():
        print(f"  - {name}: {url}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
