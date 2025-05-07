"""
Public User Web Routes Module

This module handles public web routes for user authentication and test endpoints.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# Set up templates
templates_path = os.path.join(os.path.dirname(__file__), "user", "templates")
templates = Jinja2Templates(directory=templates_path)

public_user_router = APIRouter(
    prefix="/public-user",  # Changed prefix to avoid /user/* auth collision
    tags=["web-user-public"],
    responses={404: {"description": "Page not found"}},
)


@public_user_router.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    """
    Render the login page.
    """
    return templates.TemplateResponse("login.html", {"request": request})


@public_user_router.get("/register", response_class=HTMLResponse)
async def register_view(request: Request):
    """
    Render the registration page.
    """
    return templates.TemplateResponse("register.html", {"request": request})


@public_user_router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_view(request: Request):
    """
    Render the forgot password page.
    """
    # TODO: Implement forgot password template
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Forgot password functionality coming soon!"},
    )


@public_user_router.get("/public-test", response_class=HTMLResponse)
async def public_test_view(request: Request):
    """
    Public test route to confirm no authentication is required.
    """
    return HTMLResponse(
        "<h1>This is a public test route. No authentication required.</h1>"
    )
