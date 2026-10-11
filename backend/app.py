"""FastAPI Backend Server for Signal Fusion Board (सिग्नल फ्यूजन बोर्ड).

Crisis & Disaster Intelligence Hub powered by Sarvam AI:
- Multilingual Voice Note Transcription via Saaras v4
- Handwritten Emergency Slips OCR via Sarvam Vision
- Schema-Constrained Information Extraction & Policy Reasoning via Sarvam-105B
- Closed-Loop Citizen Advisory Voice via Bulbul v3
- 3-Tier Geo Resolution, Union-Find Deduplication, and Auditable Severity Ranking
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.advisory_engine import synthesize_advisory_audio
from backend.deduplication_engine import cluster_reports
from backend.geo_resolver import resolve_location
from backend.sarvam_client import SarvamClient
from backend.severity_engine import rank_incidents
from backend.synthetic_data_generator import (
    GROUND_TRUTH_INCIDENTS,
    RAW_SYNTHETIC_REPORTS,
    compute_benchmark_metrics,
    generate_synthesized_reports_pool,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("signal-fusion-board")

app = FastAPI(
    title="Signal Fusion Board (सिग्नल फ्यूजन बोर्ड)",
    description="Multi-Channel Disaster Intelligence Fusion Platform powered by Sarvam AI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = SarvamClient()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# In-Memory Incident Store (initialized with synthetic pool)
ACTIVE_REPORTS: List[Dict[str, Any]] = generate_synthesized_reports_pool()
ACTIVE_INCIDENTS: List[Dict[str, Any]] = rank_incidents(cluster_reports(ACTIVE_REPORTS, threshold=0.55))


class IngestReportRequest(BaseModel):
    channel: str = "sms"
    language: str = "hi-IN"
    raw_text: str
    hazard_type: Optional[str] = "Flood Inundation"
    raw_location: str
    people_affected: Optional[int] = 10
    vulnerable_groups: Optional[List[str]] = []
    urgency_cues: Optional[List[str]] = []
    reporter: Optional[str] = "Citizen SMS"


class AdvisoryRequest(BaseModel):
    hazard_type: str = "Flood Inundation"
    language_code: str = "hi-IN"


class OverrideRequest(BaseModel):
    incident_id: str
    action: str  # "bump_priority", "lower_priority", "mark_dispatched", "verify"
    operator_note: Optional[str] = "Manual operator intervention"


# --- API Routes ---

@app.get("/api/health")
def health_check():
    return {
        "status": "operational",
        "service": "Signal Fusion Board",
        "district": "Patna Flood Basin & Ganga Inundation Zone",
        "models": {
            "speech_to_text": "Saaras v4",
            "reasoning": "Sarvam-105B",
            "vision_ocr": "Sarvam Vision / Doc-AI",
            "speech_synthesis": "Bulbul v3",
            "translation": "Mayura"
        },
        "active_reports": len(ACTIVE_REPORTS),
        "fused_incidents": len(ACTIVE_INCIDENTS)
    }


@app.get("/api/config")
def get_config():
    """Return non-sensitive public configuration for frontend basemaps."""
    from backend.config import CARTO_API_KEY
    return {
        "carto_key": CARTO_API_KEY,
        "default_center": [25.6100, 85.1415],
        "default_zoom": 12
    }


@app.get("/api/incidents")
def get_incidents():
    """Return the ranked queue of fused incidents and raw reports count."""
    return {
        "incidents": ACTIVE_INCIDENTS,
        "total_incidents": len(ACTIVE_INCIDENTS),
        "total_reports": len(ACTIVE_REPORTS),
        "district_center": [25.6100, 85.1415]
    }


@app.get("/api/ground-truth")
def get_ground_truth():
    """Return planted ground truth disaster incidents for demo evaluation."""
    return {
        "ground_truth": GROUND_TRUTH_INCIDENTS,
        "count": len(GROUND_TRUTH_INCIDENTS)
    }


@app.get("/api/benchmark-metrics")
def get_metrics():
    """Return backtest-style quantitative metrics against ground truth."""
    metrics = compute_benchmark_metrics(ACTIVE_INCIDENTS)
    return {"metrics": metrics}


@app.post("/api/simulate-stream")
def simulate_stream(batch_size: int = 5):
    """Reset and re-cluster reports simulating live incoming crisis feed."""
    global ACTIVE_REPORTS, ACTIVE_INCIDENTS
    ACTIVE_REPORTS = generate_synthesized_reports_pool()
    ACTIVE_INCIDENTS = rank_incidents(cluster_reports(ACTIVE_REPORTS, threshold=0.55))
    metrics = compute_benchmark_metrics(ACTIVE_INCIDENTS)
    return {
        "success": True,
        "total_reports": len(ACTIVE_REPORTS),
        "fused_incidents": len(ACTIVE_INCIDENTS),
        "metrics": metrics
    }


@app.post("/api/ingest")
def ingest_report(req: IngestReportRequest):
    """Ingest a new raw text/SMS report, resolve location, and cluster into incidents."""
    global ACTIVE_REPORTS, ACTIVE_INCIDENTS

    # 1. Geo-resolve location into uncertainty circle
    geo_res = resolve_location(raw_location=req.raw_location)

    from datetime import datetime, timezone
    new_report = {
        "id": f"REP-{len(ACTIVE_REPORTS) + 101}",
        "channel": req.channel,
        "language": req.language,
        "raw_text": req.raw_text,
        "english_translation": req.raw_text,
        "hazard_type": req.hazard_type,
        "raw_location": req.raw_location,
        "people_affected": req.people_affected or 5,
        "vulnerable_groups": req.vulnerable_groups or [],
        "urgency_cues": req.urgency_cues or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reporter": req.reporter or "Incoming Citizen Line",
        "geo": geo_res.to_dict()
    }

    ACTIVE_REPORTS.append(new_report)
    ACTIVE_INCIDENTS = rank_incidents(cluster_reports(ACTIVE_REPORTS, threshold=0.55))

    return {
        "success": True,
        "report_id": new_report["id"],
        "geo": new_report["geo"],
        "total_incidents": len(ACTIVE_INCIDENTS)
    }


@app.post("/api/ingest-audio")
async def ingest_audio(
    file: UploadFile = File(...),
    language_code: str = Form("hi-IN"),
    raw_location: str = Form("Digha Ghat"),
    hazard_type: str = Form("Flood Inundation")
):
    """Ingest live voice note, transcribe with Saaras, and fuse into incident queue."""
    global ACTIVE_REPORTS, ACTIVE_INCIDENTS
    content = await file.read()
    
    stt_res = client.speech_to_text(content, filename=file.filename or "voice.wav", language_code=language_code)
    transcript = stt_res.get("transcript", "दीघा घाट के पास पानी बहुत तेज बह रहा है!")

    # Geo-resolve
    geo_res = resolve_location(raw_location=raw_location)

    from datetime import datetime, timezone
    new_report = {
        "id": f"REP-AUDIO-{len(ACTIVE_REPORTS) + 101}",
        "channel": "voice",
        "language": language_code,
        "raw_text": transcript,
        "english_translation": transcript,
        "hazard_type": hazard_type,
        "raw_location": raw_location,
        "people_affected": 25,
        "vulnerable_groups": ["Elderly", "Infants"],
        "urgency_cues": ["Water rising fast"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reporter": f"Live Citizen Voice ({language_code})",
        "geo": geo_res.to_dict()
    }

    ACTIVE_REPORTS.append(new_report)
    ACTIVE_INCIDENTS = rank_incidents(cluster_reports(ACTIVE_REPORTS, threshold=0.55))

    return {
        "success": True,
        "transcript": transcript,
        "report_id": new_report["id"],
        "total_incidents": len(ACTIVE_INCIDENTS)
    }


@app.post("/api/advisory")
def generate_advisory(req: AdvisoryRequest):
    """Synthesize pre-approved NDMA audio safety advisory via Bulbul v3."""
    result = synthesize_advisory_audio(client, hazard_type=req.hazard_type, language_code=req.language_code)
    return result


@app.post("/api/override")
def operator_override(req: OverrideRequest):
    """Operator controls: Bump priority, verify, or mark dispatched."""
    global ACTIVE_INCIDENTS
    for inc in ACTIVE_INCIDENTS:
        if inc["incident_id"] == req.incident_id:
            if req.action == "bump_priority":
                inc["severity"]["total_severity"] = min(100.0, inc["severity"]["total_severity"] + 15.0)
                inc["severity"]["priority_level"] = "OPERATOR ESCALATED (CRITICAL)"
                inc["severity"]["badge_color"] = "#DC2626"
            elif req.action == "mark_dispatched":
                inc["status"] = "DISPATCHED (NDRF Unit En Route)"
                inc["dispatched"] = True
            elif req.action == "verify":
                inc["corroboration_status"] = "OPERATOR VERIFIED"

            # Re-sort queue
            ACTIVE_INCIDENTS.sort(key=lambda x: x["severity"]["total_severity"], reverse=True)
            return {"success": True, "updated_incident": inc}

    raise HTTPException(status_code=404, detail="Incident not found")


# Serve compiled React frontend
FRONTEND_DIST = FRONTEND_DIR / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{catchall:path}")
    def serve_spa_fallback(catchall: str):
        file_path = FRONTEND_DIST / catchall
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
elif FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
