"""FastAPI app entrypoint."""
from dotenv import load_dotenv
load_dotenv()  # Must happen before any module reads os.environ

from fastapi import FastAPI
from src.routes.extract import router as extract_router

app = FastAPI(
    title="Receipt Extractor API",
    description="Extracts structured fields from messy receipt text using an LLM.",
    version="0.1.0",
)

app.include_router(extract_router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "receipt-extractor-api"}