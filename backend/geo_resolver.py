"""3-Tier Geo-Resolution Engine for Crisis Reports.

Tier 1: EXIF / Explicit GPS
Tier 2: Gazetteer Fuzzy Match on OSM data (with script-to-Latin transliteration)
Tier 3: Landmark-Relative Proximity Buffer with Uncertainty Circles
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from backend.gazetteer import (
    DISTRICT_BOUNDS,
    LANDMARKS,
    calculate_offset,
    match_landmark,
    parse_relative_direction,
)


class GeoResolutionResult:
    def __init__(
        self,
        lat: float,
        lng: float,
        uncertainty_radius_m: float,
        tier: str,
        matched_landmark_name: Optional[str] = None,
        confidence: float = 0.8
    ):
        self.lat = lat
        self.lng = lng
        self.uncertainty_radius_m = uncertainty_radius_m
        self.tier = tier
        self.matched_landmark_name = matched_landmark_name
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": round(self.lat, 6),
            "lng": round(self.lng, 6),
            "uncertainty_radius_m": int(self.uncertainty_radius_m),
            "tier": self.tier,
            "matched_landmark": self.matched_landmark_name,
            "confidence": round(self.confidence, 2)
        }


def resolve_location(
    raw_location: str,
    explicit_coords: Optional[Tuple[float, float]] = None,
    relative_constraints: Optional[Dict[str, Any]] = None
) -> GeoResolutionResult:
    """Resolve report location into an uncertainty circle."""
    
    # --- Tier 1: Explicit Coordinates / EXIF ---
    if explicit_coords and len(explicit_coords) == 2:
        lat, lng = explicit_coords
        if DISTRICT_BOUNDS["lat_min"] <= lat <= DISTRICT_BOUNDS["lat_max"] and DISTRICT_BOUNDS["lng_min"] <= lng <= DISTRICT_BOUNDS["lng_max"]:
            return GeoResolutionResult(
                lat=lat,
                lng=lng,
                uncertainty_radius_m=35.0,  # Precision GPS buffer
                tier="tier_1_gps",
                matched_landmark_name="GPS / EXIF Sensor Fix",
                confidence=0.98
            )

    # --- Tier 3: Landmark-Relative Constraint Buffer ---
    if relative_constraints and relative_constraints.get("anchor_landmark"):
        anchor_name = relative_constraints.get("anchor_landmark", "")
        matched_lm = match_landmark(anchor_name) or match_landmark(raw_location)
        if matched_lm:
            dist_m = float(relative_constraints.get("distance_meters", 350.0))
            direction_str = str(relative_constraints.get("relative_direction", "east"))
            bearing = parse_relative_direction(direction_str)
            
            # Compute new center with offset
            new_lat, new_lng = calculate_offset(matched_lm["lat"], matched_lm["lng"], bearing, dist_m)
            # Uncertainty expands proportionally with distance
            radius = matched_lm["base_uncertainty_m"] + (dist_m * 0.45)
            
            return GeoResolutionResult(
                lat=new_lat,
                lng=new_lng,
                uncertainty_radius_m=radius,
                tier="tier_3_relative_landmark",
                matched_landmark_name=f"{dist_m:.0f}m {direction_str} of {matched_lm['name']}",
                confidence=0.82
            )

    # Check for inline regex distance & landmark in raw_location text (e.g. "500m behind Digha Ghat")
    dist_match = re.search(r"(\d{2,4})\s*(?:m|meter|मीटर|মিটার)", raw_location, re.IGNORECASE)
    if dist_match:
        dist_val = float(dist_match.group(1))
        matched_lm = match_landmark(raw_location)
        if matched_lm:
            bearing = 135.0  # generic offset
            new_lat, new_lng = calculate_offset(matched_lm["lat"], matched_lm["lng"], bearing, dist_val)
            return GeoResolutionResult(
                lat=new_lat,
                lng=new_lng,
                uncertainty_radius_m=matched_lm["base_uncertainty_m"] + (dist_val * 0.5),
                tier="tier_3_relative_landmark",
                matched_landmark_name=f"~{dist_val:.0f}m from {matched_lm['name']}",
                confidence=0.80
            )

    # --- Tier 2: Gazetteer Fuzzy Match on OSM Nodes ---
    matched_lm = match_landmark(raw_location)
    if matched_lm:
        return GeoResolutionResult(
            lat=matched_lm["lat"],
            lng=matched_lm["lng"],
            uncertainty_radius_m=matched_lm["base_uncertainty_m"],
            tier="tier_2_gazetteer",
            matched_landmark_name=matched_lm["name"],
            confidence=0.88
        )

    # --- Fallback: District Centroid with Broad Uncertainty Buffer ---
    center_lat, center_lng = DISTRICT_BOUNDS["center"]
    return GeoResolutionResult(
        lat=center_lat,
        lng=center_lng,
        uncertainty_radius_m=1800.0,
        tier="tier_fallback_district",
        matched_landmark_name=f"Unresolved mention: '{raw_location}' (District Wide)",
        confidence=0.45
    )
