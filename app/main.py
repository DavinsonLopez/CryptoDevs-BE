from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import Base, engine
from app.config.messages import SystemMessages
from app.routers import users_router, visitors_router, access_logs_router, incidents_router
from app.routers.qr_codes import router as qr_codes_router
from app.services.scheduler_service import init_scheduler
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar todos los modelos para que SQLAlchemy los reconozca
import app.models

# Crear todas las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CryptoDevs-BE",
    description="BE hecho con Python software de control de ingresos y salidas de una empresa",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173", "http://localhost:62902", "http://127.0.0.1:5173", "http://127.0.0.1:62902"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add routers
app.include_router(users_router)
app.include_router(visitors_router)
app.include_router(access_logs_router)
app.include_router(incidents_router)
app.include_router(qr_codes_router)

# Inicializar el programador de tareas
scheduler = init_scheduler()

@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación"""
    try:
        # Iniciar el programador
        scheduler.start()
        logger.info("Programador de tareas iniciado correctamente")
    except Exception as e:
        logger.error(f"Error al iniciar el programador de tareas: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento que se ejecuta al detener la aplicación"""
    try:
        # Detener el programador
        scheduler.shutdown()
        logger.info("Programador de tareas detenido correctamente")
    except Exception as e:
        logger.error(f"Error al detener el programador de tareas: {str(e)}")

# Endpoint para enviar manualmente el informe (solo para pruebas)
@app.post("/admin/send-weekly-report", tags=["Admin"])
async def send_report_manually(background_tasks: BackgroundTasks):
    """Endpoint para enviar manualmente el informe semanal (solo para pruebas)"""
    from app.services.scheduler_service import send_weekly_report, get_admin_emails
    from app.services.email_service import send_access_report_email
    
    try:
        # Obtener correos de administradores desde la configuración
        admin_emails = get_admin_emails()
        
        if not admin_emails:
            logger.error("No hay correos de administradores configurados en ADMIN_EMAILS. Usando correo por defecto.")
            admin_emails = ["sascryptodevs@gmail.com"]
        
        logger.info(f"Enviando correo a los siguientes administradores: {admin_emails}")
                
        # Intentar enviar el informe completo
        await send_weekly_report()
        
        return JSONResponse(
            status_code=200,
            content={"message": "Informe semanal enviado correctamente"}
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error al enviar el informe manualmente: {error_msg}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al enviar el informe: {error_msg}"}
        )

@app.get("/health")
async def health_check():
    return {
        "status": SystemMessages.HEALTH_CHECK_STATUS,
        "message": SystemMessages.HEALTH_CHECK_MESSAGE
    }
