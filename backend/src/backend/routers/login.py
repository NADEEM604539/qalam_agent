from fastapi import APIRouter
from backend.DTO.login import Login_request
from backend.services.login import login, register, get_user
from backend.web_scraping.playwright_login import login_to_qalam
from playwright.async_api import Page
from backend.web_scraping.playwright_get_courses import get_enrolled_courses
from fastapi import HTTPException
from playwright.async_api import async_playwright

router = APIRouter(
    prefix="/login",
    tags=["login"]
)

@router.post("/")
async def login_Request(request: Login_request):
    qalam_login=False
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        qalam_login = await login_to_qalam(page=page, email=request.email, password=request.password)
        await browser.close()
    if qalam_login:
        user = await get_user(request.email)
        if user:
            results = await login(request=request)
        else:
            results = await register(request=request)
        return results
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid Credentials"   
        )
        