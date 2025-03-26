from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from app import models, schemas
from app.database import engine, get_db
from app.config.messages import UserMessages, SystemMessages

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

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Validación manual para usuarios admin sin contraseña
        if user.user_type == 'admin' and (not user.password or len(user.password) == 0):
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED
            )

        db_user = models.User(**user.model_dump())
        db.add(db_user)
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
            raise HTTPException(
                status_code=400,
                detail=UserMessages.ERROR_DATABASE_VALIDATION
            )

@app.get("/users/", response_model=List[schemas.User])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.put("/users/{user_id}", response_model=schemas.User)
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

@app.delete("/users/{user_id}", response_model=Dict[str, str])
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
