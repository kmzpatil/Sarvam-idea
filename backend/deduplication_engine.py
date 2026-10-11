"""Online Deduplication and Clustering Engine for Crisis Reports.

Uses:
- Spatial overlap over uncertainty circles (Gaussian decay)
- Temporal exponential decay
- Semantic & hazard type similarity
- Union-Find data structure for clustering incoming reports into verified Incidents
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate Great Circle distance in meters between two coordinates."""
    r = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class UnionFind:
    """Disjoint-set data structure with path compression and union by rank."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i == root_j:
            return False

        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1
        return True


def compute_report_similarity(r1: Dict[str, Any], r2: Dict[str, Any]) -> float:
    """Compute 3-term composite similarity between two incident reports."""
    
    # 1. Spatial Overlap Term
    geo1 = r1["geo"]
    geo2 = r2["geo"]
    dist_m = haversine_distance_m(geo1["lat"], geo1["lng"], geo2["lat"], geo2["lng"])
    
    sigma1 = max(float(geo1["uncertainty_radius_m"]), 50.0)
    sigma2 = max(float(geo2["uncertainty_radius_m"]), 50.0)
    combined_sigma = math.sqrt(sigma1**2 + sigma2**2)
    
    # Gaussian spatial decay
    s_spatial = math.exp(-(dist_m**2) / (2.0 * (combined_sigma**2)))
    
    # 2. Temporal Decay Term (hours diff)
    t1 = datetime.fromisoformat(r1["timestamp"]) if isinstance(r1["timestamp"], str) else r1["timestamp"]
    t2 = datetime.fromisoformat(r2["timestamp"]) if isinstance(r2["timestamp"], str) else r2["timestamp"]
    delta_hours = abs((t1 - t2).total_seconds()) / 3600.0
    s_time = math.exp(-delta_hours / 8.0)  # 8-hour half-window
    
    # 3. Hazard & Semantic Overlap Term
    h1 = r1.get("hazard_type", "Flood").lower()
    h2 = r2.get("hazard_type", "Flood").lower()
    if h1 == h2:
        s_hazard = 1.0
    elif any(k in h1 for k in ["flood", "water", "inundat"]) and any(k in h2 for k in ["flood", "water", "inundat"]):
        s_hazard = 0.85
    elif "stranded" in h1 or "stranded" in h2:
        s_hazard = 0.70
    else:
        s_hazard = 0.30

    # Token overlap of location mentions
    tokens1 = set(r1.get("raw_location", "").lower().split())
    tokens2 = set(r2.get("raw_location", "").lower().split())
    jaccard = len(tokens1 & tokens2) / max(len(tokens1 | tokens2), 1)
    
    s_semantic = 0.7 * s_hazard + 0.3 * jaccard
    
    # Composite Weighted Similarity
    composite = (0.55 * s_spatial) + (0.15 * s_time) + (0.30 * s_semantic)
    return composite


def cluster_reports(reports: List[Dict[str, Any]], threshold: float = 0.58) -> List[Dict[str, Any]]:
    """Cluster raw reports into deduplicated Incidents using Union-Find."""
    n = len(reports)
    if n == 0:
        return []

    uf = UnionFind(n)

    # Compare pairwise candidates
    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_report_similarity(reports[i], reports[j])
            if sim >= threshold:
                uf.union(i, j)

    # Group reports by cluster root
    clusters: Dict[int, List[Dict[str, Any]]] = {}
    for i in range(n):
        root = uf.find(i)
        clusters.setdefault(root, []).append(reports[i])

    incidents = []
    for cluster_id, rep_list in clusters.items():
        incidents.append(fuse_cluster_into_incident(cluster_id, rep_list))

    return incidents


def fuse_cluster_into_incident(cluster_id: int, rep_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fuse multiple clustered reports into a single canonical Incident."""
    # Weighted centroid based on inverse variance (uncertainty radius)
    total_weight = 0.0
    weighted_lat = 0.0
    weighted_lng = 0.0
    min_uncertainty = 9999.0

    channels: Set[str] = set()
    languages: Set[str] = set()
    total_people = 0
    vulnerable_tags: Set[str] = set()
    urgency_cues: Set[str] = set()

    hazard_counts: Dict[str, int] = {}
    location_names: List[str] = []

    for rep in rep_list:
        geo = rep["geo"]
        radius = max(float(geo["uncertainty_radius_m"]), 20.0)
        weight = 1.0 / (radius**2)
        
        weighted_lat += geo["lat"] * weight
        weighted_lng += geo["lng"] * weight
        total_weight += weight
        
        min_uncertainty = min(min_uncertainty, radius)
        channels.add(rep.get("channel", "sms"))
        languages.add(rep.get("language", "hi"))
        
        total_people = max(total_people, rep.get("people_affected", 1))
        for v in rep.get("vulnerable_groups", []):
            vulnerable_tags.add(v)
        for u in rep.get("urgency_cues", []):
            urgency_cues.add(u)
            
        hz = rep.get("hazard_type", "Flood Inundation")
        hazard_counts[hz] = hazard_counts.get(hz, 0) + 1
        
        if geo.get("matched_landmark"):
            location_names.append(geo["matched_landmark"])

    canonical_lat = weighted_lat / total_weight if total_weight > 0 else rep_list[0]["geo"]["lat"]
    canonical_lng = weighted_lng / total_weight if total_weight > 0 else rep_list[0]["geo"]["lng"]
    
    # Uncertainty tightens as independent reports corroborate
    fused_radius = max(min_uncertainty * (1.0 / math.sqrt(len(rep_list))), 40.0)
    primary_hazard = max(hazard_counts, key=hazard_counts.get) if hazard_counts else "Flood Inundation"
    primary_location = location_names[0] if location_names else rep_list[0].get("raw_location", "Unknown Location")

    # Corroboration Status
    num_channels = len(channels)
    if len(rep_list) >= 3 and num_channels >= 2:
        corroboration_status = f"HIGHLY CORROBORATED ({len(rep_list)} reports across {num_channels} channels)"
    elif len(rep_list) >= 2:
        corroboration_status = f"CORROBORATED ({len(rep_list)} reports)"
    else:
        corroboration_status = "UNVERIFIED (Single Source)"

    return {
        "incident_id": f"INC-{cluster_id + 101:03d}",
        "title": f"{primary_hazard} at {primary_location}",
        "hazard_type": primary_hazard,
        "location_summary": primary_location,
        "geo": {
            "lat": round(canonical_lat, 6),
            "lng": round(canonical_lng, 6),
            "uncertainty_radius_m": int(fused_radius),
        },
        "reports_count": len(rep_list),
        "channels": list(channels),
        "languages": list(languages),
        "people_affected_estimate": total_people,
        "vulnerable_groups": list(vulnerable_tags),
        "urgency_cues": list(urgency_cues),
        "corroboration_status": corroboration_status,
        "first_reported_at": min(r["timestamp"] for r in rep_list),
        "last_reported_at": max(r["timestamp"] for r in rep_list),
        "evidence_reports": rep_list
    }
