"""
Core Web Router - Handles basic web routes and Jinja template rendering

This module contains the core web routes for the CSA Platform, including:
- Home page
- Favicon
- Certificate installer
- Other application-wide web routes
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# Create router for core web routes
router = APIRouter(
    tags=["web-core"], responses={404: {"description": "Page not found"}}
)

# Templates - Use core templates
templates = Jinja2Templates(directory="src/web/core/templates")


@router.get("/")
async def home(request: Request):
    """Application home page"""
    return templates.TemplateResponse(request=request, name="home.html")


@router.get("/favicon.ico")
async def favicon(request: Request):
    """Serve favicon"""
    return FileResponse("src/assets/favicon.ico")


@router.get("/install-certificate")
async def certificate_installer(request: Request):
    """Certificate installer page"""
    return FileResponse("src/web/core/static/cert-installer.html")


@router.get("/cert-download")
async def download_certificate(request: Request, install: bool = False):
    """
    Serve SSL certificate for download or direct installation
    When install=True, sets Content-Type that triggers Windows certificate installer
    """
    cert_path = ".cert/cert.pem"

    # Check if certificate file exists
    if not os.path.isfile(cert_path):
        return Response(content="Certificate file not found", status_code=404)

    # Read certificate content
    with open(cert_path, "rb") as cert_file:
        cert_content = cert_file.read()

    # Create response with appropriate headers
    response = Response(content=cert_content)

    if install:
        # Content type that triggers Windows certificate installer
        response.headers["Content-Type"] = "application/x-x509-ca-cert"
    else:
        # Standard download
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["Content-Disposition"] = "attachment; filename=CSAHello.crt"

    return response
