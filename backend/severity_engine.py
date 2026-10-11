"""Transparent Mathematical Severity Ranking Engine for Signal Fusion Board.

Formula:
Severity = w_people * PeopleAffected + w_vuln * VulnerableCount +
           w_hazard * HazardWeight + w_rising * RisingCues +
           w_corrob * (IndependentChannels - 1) + w_geo * GeoConfidence
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

HAZARD_WEIGHTS = {
    "Bridge Collapse": 25.0,
    "Embankment Breach": 24.0,
    "Submerged Hospital / Critical Care": 23.0,
    "Substation Electrocution Risk": 20.0,
    "Flash Flood / Trapped on Roof": 18.0,
    "Riverfront Slum Inundation": 15.0,
    "Road Washout / Transit Delay": 8.0,
    "Urban Waterlogging": 6.0,
    "Default": 12.0
}


def compute_severity_score(incident: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate mathematically transparent severity score and rationale."""
    
    # 1. People Affected (max 25 pts)
    people = max(int(incident.get("people_affected_estimate", 1)), 1)
    # Logarithmic scaling so 50 people scores ~18 pts, 200+ scores 25 pts
    score_people = min(25.0, math.log10(people + 1) * 10.5)

    # 2. Vulnerability Score (max 20 pts)
    vuln_groups = incident.get("vulnerable_groups", [])
    score_vuln = min(20.0, len(vuln_groups) * 6.5)

    # 3. Hazard Severity Weight (max 25 pts)
    hazard_type = incident.get("hazard_type", "Default")
    score_hazard = HAZARD_WEIGHTS.get(hazard_type, HAZARD_WEIGHTS["Default"])

    # 4. Rising Hazard & Urgency Cues (max 15 pts)
    urgency_cues = incident.get("urgency_cues", [])
    score_rising = min(15.0, len(urgency_cues) * 5.0)

    # 5. Multi-Channel Corroboration (max 15 pts)
    channels = incident.get("channels", [])
    rep_count = incident.get("reports_count", 1)
    channel_bonus = max(0, len(channels) - 1) * 6.0
    volume_bonus = min(rep_count, 5) * 1.5
    score_corrob = min(15.0, channel_bonus + volume_bonus)

    # Total Raw Score (capped at 100)
    total_raw = score_people + score_vuln + score_hazard + score_rising + score_corrob
    total_score = max(5.0, min(100.0, round(total_raw, 1)))

    # Priority Tier Classification
    if total_score >= 80:
        priority_level = "CRITICAL (Immediate NDRF / SDRF Dispatch)"
        badge_color = "#EF4444"  # Red
    elif total_score >= 60:
        priority_level = "HIGH (Rapid Response Team)"
        badge_color = "#F97316"  # Orange
    elif total_score >= 40:
        priority_level = "MEDIUM (Civil Defense Monitoring)"
        badge_color = "#EAB308"  # Yellow
    else:
        priority_level = "LOW (Advisory & Verification)"
        badge_color = "#3B82F6"  # Blue

    # Generate Explainable Rationale
    rationale_parts = []
    if people > 10:
        rationale_parts.append(f"~{people} individuals impacted")
    if vuln_groups:
        rationale_parts.append(f"presence of {', '.join(vuln_groups)}")
    if urgency_cues:
        rationale_parts.append(f"active cues: {', '.join(urgency_cues)}")
    if len(channels) > 1:
        rationale_parts.append(f"corroborated across {len(channels)} distinct channels ({', '.join(channels)})")
    else:
        rationale_parts.append("single-source report awaiting field corroboration")

    rationale_text = f"Priority driven by {hazard_type} with " + "; ".join(rationale_parts) + "."

    breakdown = {
        "people_score": round(score_people, 1),
        "vulnerability_score": round(score_vuln, 1),
        "hazard_score": round(score_hazard, 1),
        "urgency_score": round(score_rising, 1),
        "corroboration_score": round(score_corrob, 1),
        "total_severity": total_score,
        "priority_level": priority_level,
        "badge_color": badge_color,
        "rationale": rationale_text
    }

    return breakdown


def rank_incidents(incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank all incidents by severity score descending."""
    ranked = []
    for inc in incidents:
        severity_data = compute_severity_score(inc)
        ranked.append({
            **inc,
            "severity": severity_data
        })

    # Sort descending: Highest severity at top of queue
    ranked.sort(key=lambda x: x["severity"]["total_severity"], reverse=True)
    return ranked
