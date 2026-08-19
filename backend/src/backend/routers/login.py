from fastapi import APIRouter
from backend.DTO.login import Login_request
from backend.services.login import login, register, get_user

router = APIRouter(
    prefix="/login",
    tags=["login"]
)

@router.post("/")
async def login_Request(request: Login_request):
    user = await get_user(request.email)
    if user:
        results = await login(request=request)
    else:
        results = await register(request=request)
    print(user)
    return user


