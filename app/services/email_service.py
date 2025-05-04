from fastapi import BackgroundTasks
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración del servidor de correo
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "sascryptodevs@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "mjox howh iiku yozi")
MAIL_FROM = os.getenv("MAIL_FROM", "sascryptodevs@gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "CryptoDevs Access Control")

logger.info(f"Configuración de correo: Usuario={MAIL_USERNAME}, Servidor={MAIL_SERVER}, Puerto={MAIL_PORT}")

async def send_access_report_email(
    background_tasks: BackgroundTasks,
    subject: str,
    recipients: List[str],
    html_content: str
):
    """
    Envía un correo electrónico con el informe de accesos.
    
    Args:
        background_tasks: Tareas en segundo plano de FastAPI
        subject: Asunto del correo
        recipients: Lista de destinatarios
        html_content: Contenido HTML del correo
    """
    def _send_email():
        try:
            logger.info(f"Preparando correo para enviar a: {recipients}")
            logger.info(f"Asunto: {subject}")
            logger.info(f"Configuración: Usuario={MAIL_USERNAME}, Servidor={MAIL_SERVER}, Puerto={MAIL_PORT}")
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = f"{MAIL_FROM_NAME} <{MAIL_FROM}>"
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Contenido del mensaje
            msg.attach(MIMEText(html_content, 'html'))
            
            # Conectar al servidor SMTP
            logger.info("Conectando al servidor SMTP...")
            server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
            server.set_debuglevel(1)  # Mostrar información de depuración
            
            # Iniciar sesión
            logger.info("Iniciando sesión...")
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            
            # Enviar correo
            logger.info("Enviando correo...")
            server.send_message(msg)
            
            # Cerrar conexión
            logger.info("Cerrando conexión...")
            server.quit()
            
            logger.info("Correo enviado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    # Agregar tarea en segundo plano
    background_tasks.add_task(_send_email)
    logger.info(f"Correo programado para envío en segundo plano a: {recipients}")

async def send_user_registration_email(
    background_tasks: BackgroundTasks,
    user_email: str,
    user_name: str,
    user_document: str,
    user_position: str,
    is_admin: bool,
    user_type: str = "employee",
    qr_code_image: str = None,
    qr_code_id: int = None
):
    """
    Envía un correo electrónico de notificación de creación de cuenta.
    
    Args:
        background_tasks: Tareas en segundo plano de FastAPI
        user_email: Correo electrónico del usuario registrado
        user_name: Nombre completo del usuario registrado
        user_document: Número de documento del usuario
        user_position: Cargo del usuario
        is_admin: Si el usuario es administrador o no
    """
    subject = "Bienvenido a CryptoDevs - Cuenta Creada"
    
    # Determinar el mensaje según el tipo de usuario
    if is_admin:
        mensaje_tipo_usuario = "Como administrador, puedes iniciar sesión en el sistema utilizando tu número de documento o correo electrónico y la contraseña proporcionada."
        qr_code_html = ""  # No mostrar QR para administradores
    elif user_type == "employee":
        mensaje_tipo_usuario = "Tu código QR para acceso ha sido generado y está disponible en el sistema. Puedes usar este código para registrar tus entradas y salidas."
        # Preparar HTML para mostrar el QR como enlace directo
        if qr_code_id:
            qr_url = f"http://127.0.0.1:8000/qr-codes/image/{qr_code_id}"
            qr_code_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <p style="font-weight: bold; margin-bottom: 10px;">Tu código QR:</p>
                <img src="{qr_url}" alt="Código QR" style="width: 200px; height: 200px; border: 1px solid #ddd; padding: 10px;">
                <p style="margin-top: 10px;"><a href="{qr_url}" target="_blank" style="color: #4a69bd;">Ver código QR</a></p>
            </div>
            """
            logger.info(f"Incluyendo enlace a QR en el correo: {qr_url}")
        else:
            qr_code_html = "<p style='font-style: italic; color: #777;'>El código QR está disponible en el sistema.</p>"
    else:  # standard/visitor
        mensaje_tipo_usuario = "Tu código QR para acceso como visitante ha sido generado y está disponible en el sistema."
        # Preparar HTML para mostrar el QR como enlace directo
        if qr_code_id:
            qr_url = f"http://127.0.0.1:8000/qr-codes/image/{qr_code_id}"
            qr_code_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <p style="font-weight: bold; margin-bottom: 10px;">Tu código QR de visitante:</p>
                <img src="{qr_url}" alt="Código QR" style="width: 200px; height: 200px; border: 1px solid #ddd; padding: 10px;">
                <p style="margin-top: 10px;"><a href="{qr_url}" target="_blank" style="color: #4a69bd;">Ver código QR</a></p>
            </div>
            """
            logger.info(f"Incluyendo enlace a QR en el correo: {qr_url}")
        else:
            qr_code_html = "<p style='font-style: italic; color: #777;'>El código QR está disponible en el sistema.</p>"
    
    # Crear contenido HTML del correo
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a69bd; color: white; padding: 15px; text-align: center; }}
            .content {{ padding: 20px; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            .info {{ margin: 15px 0; }}
            .info span {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bienvenido a CryptoDevs</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{user_name}</strong>,</p>
                <p>Tu cuenta ha sido creada exitosamente en el sistema de control de acceso CryptoDevs.</p>
                
                <div class="info">
                    <p><span>Documento:</span> {user_document}</p>
                    <p><span>Nombre:</span> {user_name}</p>
                    <p><span>Cargo:</span> {user_position}</p>
                    <p><span>Correo:</span> {user_email}</p>
                    <p><span>Tipo de cuenta:</span> {'Administrador' if is_admin else ('Empleado' if user_type == 'employee' else 'Visitante')}</p>
                </div>
                
                <p>{mensaje_tipo_usuario}</p>
                
                {qr_code_html}
                
                <p>Si tienes alguna pregunta, no dudes en contactar al equipo de soporte.</p>
                
                <p>Saludos cordiales,<br>
                Equipo CryptoDevs</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no responder.</p>
                <p>&copy; {datetime.now().year} CryptoDevs. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Enviar correo
    await send_access_report_email(
        background_tasks=background_tasks,
        subject=subject,
        recipients=[user_email],
        html_content=html_content
    )
