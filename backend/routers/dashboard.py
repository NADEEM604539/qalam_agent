from fastapi import APIRouter
from src.backend.services.dashboard import get_dashboard, toggle_status
from fastapi import Depends
from src.backend.services.jwt_service import get_current_user
from src.backend.DTO.login import Status
    
router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)


@router.get('/')
async def dashboard(current_user=Depends(get_current_user)):
    dashboard_results = await get_dashboard(current_user.email)
    # Debug: print first course's marks type and first 200 chars so we
    # can confirm the data is being parsed correctly.
    if dashboard_results and dashboard_results.get("courses"):
        for c in dashboard_results["courses"]:
            print(f"[dashboard] course={c['course_id']} marks type={type(c['marks'])} len={len(c['marks'])}")
            if c['marks']:
                print(f"[dashboard] first section keys={list(c['marks'][0].keys())}")
    return dashboard_results

@router.post('/toggle_status')
async def status(request:Status, current_user=Depends(get_current_user)):
    results = await toggle_status(email=current_user.email, status=request.status)
    return results