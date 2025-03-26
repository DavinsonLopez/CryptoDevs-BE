from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.messages import SystemMessages
from app.routers import users

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

@app.get("/health")
async def health_check():
    return {
        "status": SystemMessages.HEALTH_CHECK_STATUS,
        "message": SystemMessages.HEALTH_CHECK_MESSAGE
    }

# Include routers
app.include_router(users.router)
