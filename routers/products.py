from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Product
from celery_config import celery
import shutil
import os
import uuid

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.isDeleted == False).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "createdAt": p.createdAt,
            "variants": [
                {
                    "id": v.id,
                    "color": v.color,
                    "size": v.size.value,
                    "price": v.price,
                    "stock": v.stock,
                    "img": v.img
                }
                for v in p.variants if not v.isDeleted
            ]
        }
        for p in products
    ]


@router.post("/import-csv")
async def import_products_csv(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Must be a CSV file.")

        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        task = celery.send_task("tasks.import_products_from_csv", args=[file_path])

        return {
            "message": "CSV uploaded successfully. Import started in background.",
            "task_id": task.id,
            "file_path": file_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload CSV: {str(e)}")
