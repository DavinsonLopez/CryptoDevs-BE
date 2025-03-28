from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Union
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from pydantic import ValidationError

from app import models, schemas
from app.database import get_db
from app.config.messages import UserMessages

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
