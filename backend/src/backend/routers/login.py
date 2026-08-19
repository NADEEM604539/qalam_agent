from fastapi import APIRouter

router = APIRouter(
    prefix="/login",
    tags=["login"]
)

# @router.post("/")
# def login(reqest: login_request):