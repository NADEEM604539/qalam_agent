from fastapi import APIRouter
from backend.DTO.login import Login_request
from backend.services.login import login, register, get_user
from backend.web_scraping.playwright_login import login_to_qalam
from fastapi import HTTPException

router = APIRouter(
    prefix="/login",
    tags=["login"]
)

@router.post("/")
async def login_Request(request: Login_request):
    qalam_login = await login_to_qalam(email=request.email, password=request.password)
    if qalam_login:
        user = await get_user(request.email)
        if user:
            results = await login(request=request)
        else:
            results = await register(request=request)
        print(user)
        return user
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid Credentials"   
        )
        


