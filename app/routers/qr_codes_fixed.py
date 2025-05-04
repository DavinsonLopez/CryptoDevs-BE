import io
import qrcode
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.qr_code import QRCode
from app.models.user import User
from app.models.visitor import Visitor
from app.models.access_log import AccessLog
from app.schemas.qr_code import QRCodeCreate, QRCodeResponse, QRCodeScan
import uuid
from pyzbar.pyzbar import decode
from PIL import Image

router = APIRouter(
    prefix="/qr-codes",
    tags=["QR Codes"],
    responses={404: {"description": "Not found"}},
)


@router.post("/generate/user/{user_id}", response_model=QRCodeResponse)
def generate_qr_code_for_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Generate a QR code for a user."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    
    # Generate a unique code
    code = str(uuid.uuid4())
    
    # Set expiration date (e.g., 24 hours from now)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Create QR code in database
    qr_code = QRCode(
        code=code,
        user_id=user_id,
        is_active=True,
        expires_at=expires_at,
    )
    
    db.add(qr_code)
    db.commit()
    db.refresh(qr_code)
    
    return qr_code


@router.post("/generate/visitor/{visitor_id}", response_model=QRCodeResponse)
def generate_qr_code_for_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
):
    """Generate a QR code for a visitor."""
    # Check if visitor exists
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor with id {visitor_id} not found",
        )
    
    # Generate a unique code
    code = str(uuid.uuid4())
    
    # Set expiration date (e.g., 24 hours from now)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Create QR code in database
    qr_code = QRCode(
        code=code,
        visitor_id=visitor_id,
        is_active=True,
        expires_at=expires_at,
    )
    
    db.add(qr_code)
    db.commit()
    db.refresh(qr_code)
    
    return qr_code


@router.get("/image/{qr_code_id}")
def get_qr_code_image(
    qr_code_id: int,
    db: Session = Depends(get_db),
):
    """Get QR code image for a given QR code ID."""
    # Get QR code from database
    qr_code = db.query(QRCode).filter(QRCode.id == qr_code_id).first()
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QR code with id {qr_code_id} not found",
        )
    
    # Check if QR code is active and not expired
    if not qr_code.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code is not active",
        )
    
    if qr_code.expires_at and qr_code.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code has expired",
        )
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code.code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image to bytes buffer
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return StreamingResponse(img_bytes, media_type="image/png")


@router.post("/scan", status_code=status.HTTP_200_OK)
def scan_qr_code(
    qr_scan: QRCodeScan,
    db: Session = Depends(get_db),
):
    """Scan a QR code and register access."""
    # Find QR code in database
    qr_code = db.query(QRCode).filter(QRCode.code == qr_scan.code).first()
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid QR code",
        )
    
    # Check if QR code is active and not expired
    if not qr_code.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code is not active",
        )
    
    if qr_code.expires_at and qr_code.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code has expired",
        )
    
    # Determine if this is for a user or visitor
    person_type = "employee" if qr_code.user_id else "visitor"
    person_id = qr_code.user_id if qr_code.user_id else qr_code.visitor_id
    
    # Create access log
    access_log = AccessLog(
        person_type=person_type,
        person_id=person_id,
        access_type=qr_scan.access_type,
        access_time=datetime.now(timezone.utc),
        workday_date=datetime.now(timezone.utc).date(),
        user_id=qr_code.user_id,
        visitor_id=qr_code.visitor_id,
        qr_code_id=qr_code.id,
    )
    
    db.add(access_log)
    db.commit()
    
    return {"message": f"Access {qr_scan.access_type} registered successfully"}


@router.post("/scan-image", status_code=status.HTTP_200_OK)
async def scan_qr_code_image(
    access_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Scan a QR code from an image and register access."""
    # Validate access type
    if access_type not in ["entry", "exit"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access type must be 'entry' or 'exit'",
        )
    
    # Read the image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Decode QR code
    decoded_objects = decode(image)
    if not decoded_objects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No QR code found in the image",
        )
    
    # Get the QR code data
    qr_data = decoded_objects[0].data.decode("utf-8")
    
    # Find QR code in database
    qr_code = db.query(QRCode).filter(QRCode.code == qr_data).first()
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid QR code",
        )
    
    # Check if QR code is active and not expired
    if not qr_code.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code is not active",
        )
    
    if qr_code.expires_at and qr_code.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code has expired",
        )
    
    # Determine if this is for a user or visitor
    person_type = "employee" if qr_code.user_id else "visitor"
    person_id = qr_code.user_id if qr_code.user_id else qr_code.visitor_id
    
    # Create access log
    access_log = AccessLog(
        person_type=person_type,
        person_id=person_id,
        access_type=access_type,
        access_time=datetime.now(timezone.utc),
        workday_date=datetime.now(timezone.utc).date(),
        user_id=qr_code.user_id,
        visitor_id=qr_code.visitor_id,
        qr_code_id=qr_code.id,
    )
    
    db.add(access_log)
    db.commit()
    
    return {"message": f"Access {access_type} registered successfully"}
