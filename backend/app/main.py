from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.database import get_scan, init_db, list_scans
from backend.app.models import ScanRequest, ScanResult
from backend.app.scanner import run_scan


app = FastAPI(title="AI Ad Landing Page Risk Analyzer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResult)
async def scan(request: ScanRequest) -> ScanResult:
    try:
        return await run_scan(
            str(request.url),
            dynamic=request.dynamic,
            use_llm=request.use_llm,
            cloaking=request.cloaking,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Scan failed: {exc}") from exc


@app.get("/scans")
def scans(limit: int = 20) -> list[dict]:
    return list_scans(limit=limit)


@app.get("/scans/{scan_id}", response_model=ScanResult)
def scan_detail(scan_id: int) -> ScanResult:
    result = get_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result
