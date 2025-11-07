from fastapi import APIRouter
from tasks import get_order_summary_task

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/summary")
def get_order_summary():
    task = get_order_summary_task.delay()
    return {"task_id": task.id, "status": "processing"}
