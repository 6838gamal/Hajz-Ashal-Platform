"""Server-side rendered pages for the platform-admin control panel, kept
physically inside `admin/` (per explicit product decision - see
admin/README.md) rather than the tenant-facing `templates/` directory."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="admin/templates")

router = APIRouter(include_in_schema=False)


@router.get("/admin/login", response_class=HTMLResponse)
async def platform_admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/admin", response_class=HTMLResponse)
async def platform_admin_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")
