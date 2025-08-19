# app/backend/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

def error_detail(detail):
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        # Pydantic v2 style: list of errors, each may have 'msg'
        return [{"msg": (e.get("msg") or e.get("message") or "Validation error")} for e in detail if isinstance(e, dict)]
    if isinstance(detail, dict) and "detail" in detail:
        return error_detail(detail["detail"])
    return str(detail)

async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})