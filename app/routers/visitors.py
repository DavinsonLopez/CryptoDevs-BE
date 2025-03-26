from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from sqlalchemy.exc import IntegrityError

from app import models, schemas
from app.database import get_db
from app.config.messages import VisitorMessages

router = APIRouter(
    prefix="/visitors",
    tags=["visitors"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Visitor)
def create_visitor(visitor: schemas.VisitorCreate, db: Session = Depends(get_db)):
    try:
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
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.Visitor])
def get_visitors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    visitors = db.query(models.Visitor).offset(skip).limit(limit).all()
    return visitors

@router.get("/{visitor_id}", response_model=schemas.Visitor)
def get_visitor(visitor_id: int, db: Session = Depends(get_db)):
    visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
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
        for field, value in update_data.items():
            setattr(db_visitor, field, value)

        db.commit()
        db.refresh(db_visitor)
        return db_visitor
    except IntegrityError as e:
        db.rollback()
        if "visitors_email_key" in str(e):
            raise HTTPException(
                status_code=400,
                detail=VisitorMessages.ERROR_VISITOR_EMAIL_EXISTS
            )
        raise HTTPException(status_code=400, detail=str(e))

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
