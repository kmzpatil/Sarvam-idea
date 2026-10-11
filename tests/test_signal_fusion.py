"""Comprehensive Test Suite for Signal Fusion Board (सिग्नल फ्यूजन बोर्ड).

Verifies:
1. 3-Tier Geo-Resolution with Spatial Uncertainty Circles
2. Online Union-Find Clustering & Multi-Term Similarity
3. Mathematical Severity Ranking Monotonicity & Kendall's Tau
4. NDMA Advisory Synthesis & Multi-Dialect Templates
5. FastAPI HTTP API Contract & Operator Overrides
"""

import math
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.gazetteer import LANDMARKS, match_landmark
from backend.geo_resolver import resolve_location
from backend.deduplication_engine import (
    UnionFind,
    cluster_reports,
    compute_report_similarity,
    haversine_distance_m,
)
from backend.severity_engine import compute_severity_score, rank_incidents
from backend.advisory_engine import get_advisory_for_hazard, synthesize_advisory_audio
from backend.synthetic_data_generator import (
    GROUND_TRUTH_INCIDENTS,
    RAW_SYNTHETIC_REPORTS,
    compute_benchmark_metrics,
    generate_synthesized_reports_pool,
)


# --- 1. Gazetteer & 3-Tier Geo-Resolution Tests ---

def test_gazetteer_coverage():
    """Ensure key Patna basin flood landmarks are present in gazetteer."""
    assert len(LANDMARKS) >= 10
    names = [lm["name"] for lm in LANDMARKS]
    assert "Digha Ghat" in names
    assert "Danapur Cantonment Old Bridge" in names
    assert "PMCH Hospital Emergency Gate" in names


def test_gazetteer_fuzzy_matching():
    """Test transliteration and fuzzy matches in Hindi and English."""
    # Exact English
    res1 = match_landmark("Digha Ghat")
    assert res1 is not None and res1["name"] == "Digha Ghat"

    # Hindi Devanagari
    res2 = match_landmark("दीघा घाट")
    assert res2 is not None and res2["name"] == "Digha Ghat"

    # Partial / fuzzy mention
    res3 = match_landmark("Near Digha Ghat riverfront")
    assert res3 is not None and res3["name"] == "Digha Ghat"


def test_tier1_gps_resolution():
    """Tier 1: Explicit GPS coordinates provide narrowest uncertainty (35m)."""
    res = resolve_location(raw_location="Report with GPS", explicit_coords=(25.6415, 85.0920))
    assert res.tier == "tier_1_gps"
    assert res.uncertainty_radius_m <= 40.0
    assert abs(res.lat - 25.6415) < 1e-4
    assert abs(res.lng - 85.0920) < 1e-4


def test_tier2_gazetteer_resolution():
    """Tier 2: Landmark match provides gazetteer coordinates with standard uncertainty."""
    res = resolve_location(raw_location="Near Danapur Cantonment Old Bridge")
    assert res.tier == "tier_2_gazetteer"
    assert res.uncertainty_radius_m <= 250.0
    assert res.lat > 25.0 and res.lng > 85.0


def test_tier3_landmark_offset_resolution():
    """Tier 3: Relative offset constraint calculates shifted coordinates and expands uncertainty."""
    base_res = resolve_location(raw_location="Digha Ghat")
    offset_res = resolve_location(raw_location="500m behind Digha Ghat")

    assert offset_res.tier == "tier_3_relative_landmark"
    assert offset_res.uncertainty_radius_m >= 250.0
    # Coordinates should differ slightly due to calculated offset
    dist_m = haversine_distance_m(base_res.lat, base_res.lng,
                                  offset_res.lat, offset_res.lng)
    assert 100.0 <= dist_m <= 1500.0


# --- 2. Online Union-Find Clustering & Similarity Tests ---

def test_haversine_distance():
    """Verify distance calculation between Patna nodes."""
    digha = match_landmark("Digha Ghat")
    danapur = match_landmark("Danapur Cantonment Old Bridge")
    dist = haversine_distance_m(digha["lat"], digha["lng"], danapur["lat"], danapur["lng"])
    assert 2000.0 < dist < 8000.0  # Approx 4.8 km


def test_clustering_deduplication():
    """Verify that synthetic pool of 20 reports clusters into ground truth incidents."""
    reports = generate_synthesized_reports_pool()
    incidents = cluster_reports(reports, threshold=0.55)

    # 20 raw reports must collapse into 7-9 fused clusters
    assert 6 <= len(incidents) <= 10

    # Ensure Digha Ghat reports are clustered together
    digha_incidents = [inc for inc in incidents if "Digha" in inc.get("title", "") or "Digha" in inc.get("location_summary", "")]
    assert len(digha_incidents) >= 1
    # Check that Digha has multiple corroborated reports
    assert digha_incidents[0]["reports_count"] >= 2


def test_benchmark_metrics():
    """Verify that quantitative benchmark achieves target hackathon thresholds."""
    reports = generate_synthesized_reports_pool()
    incidents = rank_incidents(cluster_reports(reports, threshold=0.55))
    metrics = compute_benchmark_metrics(incidents)

    assert metrics["total_raw_reports"] == 20
    assert metrics["dedupe_noise_reduction_pct"] >= 50.0  # At least 50% deduplication
    assert metrics["pairwise_dedupe_f1"] >= 0.85         # High F1 against planted ground truth
    assert metrics["median_geo_error_meters"] <= 180.0    # Geo accuracy within 180m
    assert metrics["severity_rank_correlation_kendall_tau"] >= 0.75


# --- 3. Severity Ranking Monotonicity Tests ---

def test_severity_calculation():
    """Test mathematical severity weighting and rationale."""
    sev_high = compute_severity_score({
        "people_affected_estimate": 150,
        "vulnerable_groups": ["Infants", "Elderly", "Dialysis Patients"],
        "hazard_type": "Embankment Breach",
        "urgency_cues": ["Water rising fast", "Immediate rescue required"],
        "channels": ["voice", "sms", "handwritten_slip"],
        "reports_count": 4,
    })

    sev_low = compute_severity_score({
        "people_affected_estimate": 5,
        "vulnerable_groups": [],
        "hazard_type": "Road Washout / Transit Delay",
        "urgency_cues": [],
        "channels": ["sms"],
        "reports_count": 1,
    })

    assert sev_high["total_severity"] > 75.0
    assert "CRITICAL" in sev_high["priority_level"]
    assert sev_low["total_severity"] < 60.0
    assert sev_high["total_severity"] > sev_low["total_severity"]
    assert "Embankment Breach" in sev_high["rationale"]


# --- 4. NDMA Advisory Synthesis Tests ---

def test_advisory_script_retrieval():
    """Verify pre-approved NDMA multi-dialect scripts."""
    script_hi = get_advisory_for_hazard("Flood Inundation", "hi-IN")
    script_bn = get_advisory_for_hazard("Flood Inundation", "bn-IN")
    script_en = get_advisory_for_hazard("Flood Inundation", "en-IN")

    assert "आपातकालीन सलाह" in script_hi["advisory_text"] or "बाढ़" in script_hi["advisory_text"]
    assert "জরুরী পরামর্শ" in script_bn["advisory_text"]
    assert "Emergency Advisory" in script_en["advisory_text"]


# --- 5. FastAPI Endpoints & Integration Tests ---

def test_api_health():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert "Saaras v4" in data["models"]["speech_to_text"]
    assert "Sarvam-105B" in data["models"]["reasoning"]


def test_api_incidents():
    client = TestClient(app)
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    data = resp.json()
    assert "incidents" in data
    assert len(data["incidents"]) > 0
    # Queue must be ordered by severity descending
    scores = [inc["severity"]["total_severity"] for inc in data["incidents"]]
    assert scores == sorted(scores, reverse=True)


def test_api_benchmark_metrics():
    client = TestClient(app)
    resp = client.get("/api/benchmark-metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert data["metrics"]["pairwise_dedupe_f1"] >= 0.85


def test_api_ingest_report():
    client = TestClient(app)
    payload = {
        "channel": "sms",
        "language": "hi-IN",
        "raw_text": "दीघा घाट के पास पानी बहुत तेज बह रहा है, 20 लोग फंसे हैं",
        "hazard_type": "Embankment Breach",
        "raw_location": "Digha Ghat",
        "people_affected": 20,
        "vulnerable_groups": ["Elderly"],
        "urgency_cues": ["Water rising fast"],
        "reporter": "Citizen SMS"
    }
    resp = client.post("/api/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "geo" in data


def test_api_operator_override():
    client = TestClient(app)
    incidents_resp = client.get("/api/incidents")
    incidents = incidents_resp.json()["incidents"]
    first_id = incidents[0]["incident_id"]

    # Test Bump Priority
    bump_resp = client.post("/api/override", json={
        "incident_id": first_id,
        "action": "bump_priority",
        "operator_note": "Field volunteer confirmed imminent danger"
    })
    assert bump_resp.status_code == 200
    updated = bump_resp.json()["updated_incident"]
    assert "ESCALATED" in updated["severity"]["priority_level"]

    # Test Mark Dispatched
    dispatch_resp = client.post("/api/override", json={
        "incident_id": first_id,
        "action": "mark_dispatched"
    })
    assert dispatch_resp.status_code == 200
    assert dispatch_resp.json()["updated_incident"]["dispatched"] is True
