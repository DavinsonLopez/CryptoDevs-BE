from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
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

@router.get("/detailed", response_model=List[schemas.AccessLogDetailed])
def get_detailed_access_logs(
    skip: int = 0,
    limit: int = 100,
    workday_date: date = None,
    db: Session = Depends(get_db)
):
    """
    Get access logs with detailed person information (employee or visitor).
    This endpoint performs a LEFT JOIN to retrieve user or visitor details along with access logs.
    """
    # Build the base query
    query = """
        SELECT 
            acl.id, 
            acl.person_type, 
            acl.person_id, 
            acl.access_type as action_type, 
            acl.access_time as timestamp, 
            acl.workday_date,
            COALESCE(us.first_name, vis.first_name) AS first_name,
            COALESCE(us.last_name, vis.last_name) AS last_name,
            COALESCE(us.document_number, vis.document_number) AS document_number,
            COALESCE(us.email, vis.email) AS email
        FROM access_logs acl
        LEFT JOIN users us ON acl.person_type = 'employee' AND acl.person_id = us.id
        LEFT JOIN visitors vis ON acl.person_type = 'visitor' AND acl.person_id = vis.id
    """
    
    # Add filter for workday_date if provided
    if workday_date:
        query += f" WHERE acl.workday_date = '{workday_date}'"
    
    # Add pagination
    query += f" ORDER BY acl.access_time DESC LIMIT {limit} OFFSET {skip}"
    
    # Execute the query
    result = db.execute(text(query))
    
    # Convert the result to a list of dictionaries
    detailed_logs = []
    for row in result:
        log = {
            "id": row.id,
            "person_type": row.person_type,
            "person_id": row.person_id,
            "action_type": row.action_type,
            "timestamp": row.timestamp,
            "workday_date": row.workday_date,
            "person_details": {
                "first_name": row.first_name,
                "last_name": row.last_name,
                "document_number": row.document_number,
                "email": row.email
            }
        }
        detailed_logs.append(log)
    
    return detailed_logs

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
