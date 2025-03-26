from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config.messages import SystemMessages
from app.routers import users_router, visitors_router, access_logs_router, incidents_router

app = FastAPI(
    title="CryptoDevs-BE",
    description="BE hecho con Python software de control de ingresos y salidas de una empresa",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(users_router)
app.include_router(visitors_router)
app.include_router(access_logs_router)
app.include_router(incidents_router)

@app.get("/health")
async def health_check():
    return {
        "status": SystemMessages.HEALTH_CHECK_STATUS,
        "message": SystemMessages.HEALTH_CHECK_MESSAGE
    }
