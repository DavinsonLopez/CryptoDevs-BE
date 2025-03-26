from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app import models, schemas
from app.database import get_db
from app.config.messages import IncidentMessages

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Incident)
def create_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db)):
    # Verify that the person exists
    if incident.person_type == 'employee':
        person = db.query(models.User).filter(models.User.id == incident.person_id).first()
    else:
        person = db.query(models.Visitor).filter(models.Visitor.id == incident.person_id).first()

    if incident.person_id and not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found"
        )

    try:
        db_incident = models.Incident(**incident.model_dump())
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        return db_incident
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.Incident])
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    incident_type: str = None,
    person_type: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Incident)
    if incident_type:
        query = query.filter(models.Incident.incident_type == incident_type)
    if person_type:
        query = query.filter(models.Incident.person_type == person_type)
    incidents = query.offset(skip).limit(limit).all()
    return incidents

@router.get("/{incident_id}", response_model=schemas.Incident)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=404,
            detail=IncidentMessages.ERROR_INCIDENT_NOT_FOUND
        )
    return incident

@router.put("/{incident_id}", response_model=schemas.Incident)
def update_incident(incident_id: int, incident: schemas.IncidentUpdate, db: Session = Depends(get_db)):
    db_incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(
            status_code=404,
            detail=IncidentMessages.ERROR_INCIDENT_NOT_FOUND
        )

    update_data = incident.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_incident, field, value)

    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.delete("/{incident_id}", response_model=Dict[str, str])
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    db_incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(
            status_code=404,
            detail=IncidentMessages.ERROR_INCIDENT_NOT_FOUND
        )
    
    db.delete(db_incident)
    db.commit()
    
    return {"message": IncidentMessages.SUCCESS_INCIDENT_DELETED}
