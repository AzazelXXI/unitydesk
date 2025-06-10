"""
Core Web Router - Handles basic web routes and Jinja template rendering

This module contains the core web routes for the CSA Platform, including:
- Home page
- Favicon
- Certificate installer
- Other application-wide web routes
"""

from fastapi import APIRouter, Request, Response, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from fastapi import Depends
import os

# Create router for core web routes
router = APIRouter(
    tags=["web-core"], responses={404: {"description": "Page not found"}}
)

# Templates - Use user templates for login/register
user_templates_path = os.path.join(os.path.dirname(__file__), "user", "templates")
user_templates = Jinja2Templates(directory=user_templates_path)

# Templates - Use core templates for other routes
templates = Jinja2Templates(directory="src/web/core/templates")


@router.get("/")
async def home(request: Request):
    """Redirect home page to the login page"""
    return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Render the login page
    """
    return user_templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle login form submission
    """
    # Import here to avoid circular imports
    from src.controllers.user_controller import login_for_access_token

    try:
        # Attempt to login
        token = await login_for_access_token(db, username, password)
        if not token:
            return user_templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error_message": "Incorrect username or password. Please try again.",
                },
            )
        # Successful login - redirect to tasks
        response = RedirectResponse(url="/tasks", status_code=303)
        # You can set cookies here if needed for remember_me functionality
        if remember_me:
            response.set_cookie(
                "remember_token", token.access_token, max_age=30 * 24 * 3600
            )  # 30 days
        return response

    except Exception as e:
        return user_templates.TemplateResponse(
            "login.html",
            {"request": request, "error_message": "Login failed. Please try again."},
        )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Render the registration page
    """
    return user_templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone_number: str = Form(None),
    department: str = Form(None),
    agree_terms: bool = Form(False),
    marketing_consent: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle registration form submission
    """
    # Import here to avoid circular imports
    from src.controllers.user_controller import create_user
    from src.schemas.user import UserCreate

    try:
        if not agree_terms:
            return user_templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error_message": "You must agree to the terms and conditions.",
                },
            )

        # Create user data
        user_data = UserCreate(
            email=email,
            name=username,  # Use 'name' field instead of 'username'
            password=password,
            user_type="user",  # Default user type
            profile=(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "display_name": f"{first_name} {last_name}",
                    "phone": phone_number,
                }
                if first_name or last_name or phone_number
                else None
            ),
        )

        # Create the user
        user = await create_user(db, user_data)

        # Successful registration - redirect to login with success message
        return RedirectResponse(
            url="/login?success=Registration successful! Please log in.",
            status_code=303,
        )

    except HTTPException as e:
        return user_templates.TemplateResponse(
            "register.html", {"request": request, "error_message": str(e.detail)}
        )
    except Exception as e:
        return user_templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error_message": "Registration failed. Please try again.",
            },
        )


@router.get("/logout")
async def logout(request: Request):
    """
    Handle logout
    """
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("remember_token")
    return response


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
