"""Server-side rendered web pages (Jinja2). These are thin wrappers that
return HTML — all logic stays in the API endpoints called by the browser JS."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/register/business", response_class=HTMLResponse)
async def register_business(request: Request):
    return templates.TemplateResponse(request=request, name="register_business.html")


@router.get("/register/client", response_class=HTMLResponse)
async def register_client(request: Request):
    return templates.TemplateResponse(request=request, name="register_client.html")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/register", response_class=RedirectResponse)
async def register_redirect():
    return RedirectResponse(url="/")
