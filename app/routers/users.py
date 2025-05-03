from fastapi import APIRouter, Depends, HTTPException, Path, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Union
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from pydantic import ValidationError, BaseModel, EmailStr
import qrcode
import io
import base64

from app import models, schemas
from app.database import get_db
from app.config.messages import UserMessages
from app.services.email_service import send_user_registration_email
from app.routers.qr_codes import generate_qr_code_for_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Validación manual para usuarios admin sin contraseña
        if user.user_type == 'admin' and (not user.password or len(user.password) == 0):
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED
            )

        # Convertir el email a minúsculas para comparación case-insensitive
        user_email_lower = user.email.lower()
        
        # Verificar si ya existe un usuario con el mismo email (case insensitive) o documento
        existing_user = db.query(models.User).filter(
            or_(
                models.User.email.ilike(user_email_lower),
                models.User.document_number == user.document_number
            )
        ).first()
        
        if existing_user:
            if existing_user.email.lower() == user_email_lower:
                raise HTTPException(
                    status_code=400,
                    detail=UserMessages.ERROR_EMAIL_EXISTS
                )
            elif existing_user.document_number == user.document_number:
                raise HTTPException(
                    status_code=400,
                    detail=UserMessages.ERROR_DOCUMENT_EXISTS
                )

        # Asegurar que el email se guarde en minúsculas para consistencia
        user_dict = user.model_dump()
        user_dict['email'] = user_email_lower
        
        db_user = models.User(**user_dict)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except ValidationError as e:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        # Capturar errores específicos incluso si no son IntegrityError
        error_msg = str(e)
        if "users_email_key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_EMAIL_EXISTS
            )
        elif "users_document_number_key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_DOCUMENT_EXISTS
            )
        elif "check" in error_msg.lower() and "admin" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED
            )
        else:
            # Extraer solo el mensaje de error sin el código
            error_message = str(e)
            # Si el mensaje tiene formato "código: mensaje", extraer solo el mensaje
            if ": " in error_message and error_message.split(": ")[0].isdigit():
                error_message = error_message.split(": ", 1)[1]
            
            raise HTTPException(
                status_code=500,
                detail=error_message
            )

@router.get("/", response_model=List[schemas.User])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.User)
def get_user_by_id(
    user_id: str = Path(..., description="ID or document number of the user"),
    db: Session = Depends(get_db)
):
    # Try to convert to int for ID search, if fails it's a document number
    try:
        id_num = int(user_id)
        user = db.query(models.User).filter(
            or_(
                models.User.id == id_num,
                models.User.document_number == user_id
            )
        ).first()
    except ValueError:
        # If conversion fails, search only by document number
        user = db.query(models.User).filter(models.User.document_number == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=UserMessages.ERROR_USER_NOT_FOUND
        )
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail=UserMessages.ERROR_USER_NOT_FOUND
            )

        # Si se está actualizando a admin, validar la contraseña
        if user_update.user_type == "admin":
            if not user_update.password or len(user_update.password) == 0:
                if not db_user.password:  # Si no tenía contraseña antes
                    raise HTTPException(
                        status_code=400,
                        detail=UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED
                    )

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except IntegrityError as e:
        db.rollback()
        if "users_email_key" in str(e):
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_EMAIL_EXISTS
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_DATABASE_VALIDATION
            )

@router.post("/login", response_model=schemas.User)
def login_user(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # Buscar usuario por email o número de documento
    user = db.query(models.User).filter(
        or_(
            models.User.email == login_data.identifier,
            models.User.document_number == login_data.identifier
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=UserMessages.ERROR_USER_NOT_FOUND
        )
    
    # Verificar que el usuario sea admin
    if user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail=UserMessages.ERROR_NOT_ADMIN
        )
    
    # Verificar contraseña
    if not user.password or user.password != login_data.password:
        raise HTTPException(
            status_code=401,
            detail=UserMessages.ERROR_INVALID_CREDENTIALS
        )

    return user


class AdminUserRegistrationRequest(BaseModel):
    document_number: str
    first_name: str
    last_name: str
    position: str
    email: EmailStr
    is_admin: bool = False
    user_type: str = "employee"  # Valor por defecto
    password: str = None


class AdminUserRegistrationResponse(BaseModel):
    user: schemas.User
    qr_code_id: int
    message: str


@router.post("/admin/register", response_model=AdminUserRegistrationResponse)
async def admin_register_user(
    user_data: AdminUserRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para que los administradores registren nuevos usuarios.
    Genera un código QR automáticamente y envía un correo de notificación.
    """
    # Validar que si es admin, debe tener contraseña
    if user_data.is_admin and (not user_data.password or len(user_data.password.strip()) == 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED
        )
    
    # Determinar el tipo de usuario
    # Si es admin, siempre será "admin" independientemente del user_type enviado
    user_type = "admin" if user_data.is_admin else user_data.user_type
    
    # Crear objeto de usuario para la base de datos
    user_create = schemas.UserCreate(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        document_number=user_data.document_number,
        email=user_data.email,
        user_type=user_type,
        password=user_data.password if user_data.is_admin else None,
        image_hash="default"  # Valor por defecto para el hash de imagen
    )
    
    try:
        # Crear el usuario
        db_user = create_user(user_create, db)
        
        # Generar código QR para el usuario
        qr_code = generate_qr_code_for_user(db_user.id, db)
        
        # Generar imagen del QR para incluir en el correo
        qr_image_base64 = None
        if not user_data.is_admin:  # Solo para usuarios no admin
            try:
                # Obtener la URL completa del QR
                qr_url = f"http://127.0.0.1:8000/qr-codes/image/{qr_code.id}"
                
                # Crear el código QR
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,  # Mayor corrección de errores
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_code.code)  # Usar el código generado
                qr.make(fit=True)
                
                # Generar imagen
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir a base64
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue())
                qr_image_base64 = img_str.decode('utf-8')
                
                print(f"QR generado correctamente para usuario {db_user.id}, longitud base64: {len(qr_image_base64)}")
            except Exception as e:
                print(f"Error al generar imagen QR: {str(e)}")
        
        # Enviar correo de notificación
        await send_user_registration_email(
            background_tasks=background_tasks,
            user_email=db_user.email,
            user_name=f"{db_user.first_name} {db_user.last_name}",
            user_document=db_user.document_number,
            user_position=user_data.position,  # Guardamos el cargo en el correo aunque no esté en el modelo
            is_admin=user_data.is_admin,
            user_type=user_type,  # Pasamos el tipo de usuario
            qr_code_id=qr_code.id  # Pasamos el ID del código QR para generar la URL
        )
        
        return {
            "user": db_user,
            "qr_code_id": qr_code.id,
            "message": "Usuario registrado exitosamente y notificación enviada por correo"
        }
        
    except HTTPException as e:
        # Re-lanzar excepciones HTTP que ya tienen el formato correcto
        raise e
    except Exception as e:
        # Capturar cualquier otro error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )


@router.delete("/{user_id}", response_model=Dict[str, str])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail=UserMessages.ERROR_USER_NOT_FOUND
        )
    
    db.delete(db_user)
    db.commit()
    
    return {"message": UserMessages.SUCCESS_USER_DELETED}
