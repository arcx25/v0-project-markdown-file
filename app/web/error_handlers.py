"""HTTP error handlers with custom error pages."""
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="app/templates")


ERROR_MESSAGES = {
    400: ("Bad Request", "The request could not be understood by the server."),
    401: ("Unauthorized", "You need to log in to access this resource."),
    403: ("Forbidden", "You don't have permission to access this resource."),
    404: ("Not Found", "The page you're looking for doesn't exist."),
    405: ("Method Not Allowed", "This action is not supported."),
    429: ("Too Many Requests", "You're making too many requests. Please slow down."),
    500: ("Internal Server Error", "Something went wrong on our end."),
    502: ("Bad Gateway", "The server received an invalid response."),
    503: ("Service Unavailable", "The service is temporarily unavailable."),
}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom error pages."""
    error_code = exc.status_code
    error_title, default_message = ERROR_MESSAGES.get(
        error_code, 
        ("Error", "An unexpected error occurred.")
    )
    error_message = exc.detail if exc.detail else default_message
    
    # For API requests, return JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=error_code,
            content={"detail": error_message}
        )
    
    # For web requests, return HTML
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": error_code,
            "error_title": error_title,
            "error_message": error_message,
        },
        status_code=error_code,
    )
