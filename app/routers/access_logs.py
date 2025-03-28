from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import date

from app import models, schemas
from app.database import get_db
from app.config.messages import AccessLogMessages

router = APIRouter(
    prefix="/access-logs",
    tags=["access_logs"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.AccessLog)
def create_access_log(access_log: schemas.AccessLogCreate, db: Session = Depends(get_db)):
    try:
        # Verify that the person exists
        if access_log.person_type == 'employee':
            person = db.query(models.User).filter(models.User.id == access_log.person_id).first()
            if not person:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró ningún empleado con el ID {access_log.person_id}"
                )
        elif access_log.person_type == 'visitor':
            person = db.query(models.Visitor).filter(models.Visitor.id == access_log.person_id).first()
            if not person:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró ningún visitante con el ID {access_log.person_id}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de persona no válido: {access_log.person_type}. Debe ser 'employee' o 'visitor'"
            )

        db_access_log = models.AccessLog(**access_log.model_dump())
        db.add(db_access_log)
        db.commit()
        db.refresh(db_access_log)
        return db_access_log
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        # Extraer solo el mensaje de error sin el código
        error_message = str(e)
        if ": " in error_message and error_message.split(": ")[0].isdigit():
            error_message = error_message.split(": ", 1)[1]
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el registro de acceso: {error_message}"
        )

@router.get("/", response_model=List[schemas.AccessLog])
def get_access_logs(
    skip: int = 0,
    limit: int = 100,
    workday_date: date = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.AccessLog)
    if workday_date:
        query = query.filter(models.AccessLog.workday_date == workday_date)
    access_logs = query.offset(skip).limit(limit).all()
    return access_logs

@router.get("/{access_log_id}", response_model=schemas.AccessLog)
def get_access_log(access_log_id: int, db: Session = Depends(get_db)):
    access_log = db.query(models.AccessLog).filter(models.AccessLog.id == access_log_id).first()
    if not access_log:
        raise HTTPException(
            status_code=404,
            detail=AccessLogMessages.ERROR_ACCESS_LOG_NOT_FOUND
        )
    return access_log

@router.put("/{access_log_id}", response_model=schemas.AccessLog)
def update_access_log(access_log_id: int, access_log: schemas.AccessLogUpdate, db: Session = Depends(get_db)):
    db_access_log = db.query(models.AccessLog).filter(models.AccessLog.id == access_log_id).first()
    if not db_access_log:
        raise HTTPException(
            status_code=404,
            detail=AccessLogMessages.ERROR_ACCESS_LOG_NOT_FOUND
        )

    update_data = access_log.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_access_log, field, value)

    db.commit()
    db.refresh(db_access_log)
    return db_access_log

@router.delete("/{access_log_id}", response_model=Dict[str, str])
def delete_access_log(access_log_id: int, db: Session = Depends(get_db)):
    db_access_log = db.query(models.AccessLog).filter(models.AccessLog.id == access_log_id).first()
    if not db_access_log:
        raise HTTPException(
            status_code=404,
            detail=AccessLogMessages.ERROR_ACCESS_LOG_NOT_FOUND
        )
    
    db.delete(db_access_log)
    db.commit()
    
    return {"message": AccessLogMessages.SUCCESS_ACCESS_LOG_DELETED}
