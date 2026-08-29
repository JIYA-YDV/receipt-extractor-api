"""FastAPI app entrypoint with custom input validation mapping."""
from dotenv import load_dotenv
load_dotenv()  # Must happen before any module reads os.environ

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.routes.extract import router as extract_router

app = FastAPI(
    title="Receipt Extractor API",
    description="Extracts structured fields from messy receipt text using an LLM.",
    version="0.1.0",
)

@app.exception_handler(RequestValidationError)
async def input_validation_handler(request: Request, exc: RequestValidationError):
    """Convert FastAPI's default 422 for input errors into a 400 that names the field."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_input",
            "field": field or "unknown",
            "message": first.get("msg", "invalid input"),
        },
    )

app.include_router(extract_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "receipt-extractor-api"}