from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Dict
from sqlalchemy.exc import IntegrityError

from app import models, schemas
from app.database import get_db
from app.config.messages import VisitorMessages
from sqlalchemy import or_

router = APIRouter(
    prefix="/visitors",
    tags=["visitors"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Visitor)
def create_visitor(visitor: schemas.VisitorCreate, db: Session = Depends(get_db)):
    try:
        # Convertir el email a minúsculas para comparación case-insensitive
        if visitor.email:
            visitor_email_lower = visitor.email.lower()
            
            # Verificar si ya existe un visitante con el mismo email (case insensitive)
            existing_visitor = db.query(models.Visitor).filter(
                models.Visitor.email.ilike(visitor_email_lower)
            ).first()
            
            if existing_visitor:
                raise HTTPException(
                    status_code=400,
                    detail=VisitorMessages.ERROR_VISITOR_EMAIL_EXISTS
                )
            
            # Asegurar que el email se guarde en minúsculas para consistencia
            visitor_dict = visitor.model_dump()
            visitor_dict['email'] = visitor_email_lower
            db_visitor = models.Visitor(**visitor_dict)
        else:
            db_visitor = models.Visitor(**visitor.model_dump())
            
        db.add(db_visitor)
        db.commit()
        db.refresh(db_visitor)
        return db_visitor
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e)
        if "visitors_email_key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=VisitorMessages.ERROR_VISITOR_EMAIL_EXISTS
            )
        elif "visitors_document_number_key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=VisitorMessages.ERROR_VISITOR_DOCUMENT_EXISTS
            )
        # Extraer solo el mensaje de error sin el código
        error_message = str(e)
        if ": " in error_message and error_message.split(": ")[0].isdigit():
            error_message = error_message.split(": ", 1)[1]
        raise HTTPException(status_code=400, detail=error_message)

@router.get("/", response_model=List[schemas.Visitor])
def get_visitors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    visitors = db.query(models.Visitor).offset(skip).limit(limit).all()
    return visitors

@router.get("/{visitor_id}", response_model=schemas.Visitor)
def get_visitor_by_id(
    visitor_id: str = Path(..., description="ID or document number of the user"),
    db: Session = Depends(get_db)
):
    try:
        id_num = int(visitor_id)
        visitor = db.query(models.Visitor).filter(
            or_(
                models.Visitor.id == id_num,
                models.Visitor.document_number == visitor_id
            )
        ).first()
    except ValueError:
        visitor = db.query(models.Visitor).filter(models.Visitor.document_number == visitor_id).first()

    if not visitor:
        raise HTTPException(
            status_code=404,
            detail=VisitorMessages.ERROR_VISITOR_NOT_FOUND
        )
    return visitor

@router.put("/{visitor_id}", response_model=schemas.Visitor)
def update_visitor(visitor_id: int, visitor: schemas.VisitorUpdate, db: Session = Depends(get_db)):
    try:
        db_visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
        if not db_visitor:
            raise HTTPException(
                status_code=404,
                detail=VisitorMessages.ERROR_VISITOR_NOT_FOUND
            )

        update_data = visitor.model_dump(exclude_unset=True)
        
        # Si se está actualizando el email, convertirlo a minúsculas y verificar duplicados
        if 'email' in update_data and update_data['email']:
            email_lower = update_data['email'].lower()
            
            # Verificar si ya existe otro visitante con el mismo email (case insensitive)
            existing_visitor = db.query(models.Visitor).filter(
                models.Visitor.email.ilike(email_lower),
                models.Visitor.id != visitor_id
            ).first()
            
            if existing_visitor:
                raise HTTPException(
                    status_code=400,
                    detail=VisitorMessages.ERROR_VISITOR_EMAIL_EXISTS
                )
                
            # Actualizar el email a minúsculas
            update_data['email'] = email_lower

        for field, value in update_data.items():
            setattr(db_visitor, field, value)

        db.commit()
        db.refresh(db_visitor)
        return db_visitor
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e)
        if "visitors_email_key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=VisitorMessages.ERROR_VISITOR_EMAIL_EXISTS
            )
        # Extraer solo el mensaje de error sin el código
        error_message = str(e)
        if ": " in error_message and error_message.split(": ")[0].isdigit():
            error_message = error_message.split(": ", 1)[1]
        raise HTTPException(status_code=400, detail=error_message)

@router.delete("/{visitor_id}", response_model=Dict[str, str])
def delete_visitor(visitor_id: int, db: Session = Depends(get_db)):
    db_visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if not db_visitor:
        raise HTTPException(
            status_code=404,
            detail=VisitorMessages.ERROR_VISITOR_NOT_FOUND
        )
    
    db.delete(db_visitor)
    db.commit()
    
    return {"message": VisitorMessages.SUCCESS_VISITOR_DELETED}
