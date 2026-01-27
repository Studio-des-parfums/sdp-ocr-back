from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.endpoints import ocr, customers, users, export, groups, login_history, customer_reviews, files, formulas, emails, roles
from app.database import get_connection

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for PDF OCR processing with Mistral",
    version="1.0.0"
)

test = get_connection()
test

# Monter les fichiers statiques
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sdp-ocr-front.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["Groups"])
app.include_router(login_history.router, prefix="/api/v1/login-history", tags=["Login History"])
app.include_router(customer_reviews.router, prefix="/api/v1/customer-reviews", tags=["Customer Reviews"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])
app.include_router(formulas.router, prefix="/api/v1/formulas", tags=["Formulas"])
app.include_router(emails.router, prefix="/api/v1/emails", tags=["Emails"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to SDP OCR Backend",
        "description": "PDF handwriting OCR service using Mistral",
        "endpoints": {
            "health": "/health",
            "upload_pdf": "/api/v1/ocr/upload-pdf",
            "customers": "/api/v1/customers",
            "users": "/api/v1/users",
            "export": "/api/v1/export",
            "groups": "/api/v1/groups",
            "login_history": "/api/v1/login-history",
            "customer_reviews": "/api/v1/customer-reviews",
            "files": "/api/v1/files",
            "formulas": "/api/v1/formulas",
            "emails": "/api/v1/emails",
            "roles": "/api/v1/roles",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SDP OCR Backend"}

# For Render deployment
if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False
    )