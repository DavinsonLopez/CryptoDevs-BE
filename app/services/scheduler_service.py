from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import EmailStr
import logging
import os
from dotenv import load_dotenv

from app.services.report_service import get_weekly_access_report, generate_html_report
from app.services.email_service import send_access_report_email
from app.database.connection import get_db
from app.models.user import User

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener lista de administradores desde la base de datos
def get_admin_emails() -> List[EmailStr]:
    """
    Obtiene la lista de correos de administradores desde la base de datos.
    Busca usuarios con user_type igual a 'admin'.
    
    Returns:
        Lista de correos electrónicos de administradores
    """
    # Obtener la sesión de base de datos
    db = next(get_db())
    
    try:
        # Consultar usuarios con user_type = 'admin'
        admin_users = db.query(User).filter(User.user_type == 'admin').all()
        
        if not admin_users:
            logger.warning("No se encontraron usuarios administradores en la base de datos")
            return []
        
        # Extraer los correos electrónicos
        admin_emails = [user.email for user in admin_users if user.email]
        
        logger.info(f"Se encontraron {len(admin_emails)} correos de administradores en la base de datos")
        return admin_emails
    
    except Exception as e:
        logger.error(f"Error al obtener correos de administradores: {str(e)}")
        return []
    
    finally:
        db.close()

async def send_weekly_report():
    """
    Tarea programada para enviar el informe semanal de accesos.
    """
    logger.info("Iniciando generación del informe semanal de accesos")
    
    # Obtener la sesión de base de datos
    db = next(get_db())
    
    try:
        # Generar el informe
        report_data = get_weekly_access_report(db)
        html_content = generate_html_report(report_data)
        
        # Obtener correos de administradores
        admin_emails = get_admin_emails()
        
        if not admin_emails:
            logger.error("No hay correos de administradores configurados. No se enviará el informe.")
            return
        
        # Crear objeto BackgroundTasks para enviar el correo
        background_tasks = BackgroundTasks()
        
        # Enviar el correo
        subject = f"Informe Semanal de Accesos ({report_data['period']['start']} al {report_data['period']['end']})"
        await send_access_report_email(
            background_tasks=background_tasks,
            subject=subject,
            recipients=admin_emails,
            html_content=html_content
        )
        
        logger.info(f"Informe semanal enviado a {len(admin_emails)} administradores")
    
    except Exception as e:
        logger.error(f"Error al generar o enviar el informe semanal: {str(e)}")
    
    finally:
        db.close()

def init_scheduler():
    """
    Inicializa el programador de tareas.
    
    Returns:
        Instancia del programador
    """
    scheduler = AsyncIOScheduler()
    
    # Programar el envío del informe semanal (cada lunes a las 8:00 AM)
    scheduler.add_job(
        send_weekly_report,
        CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_access_report",
        replace_existing=True
    )
    
    return scheduler
