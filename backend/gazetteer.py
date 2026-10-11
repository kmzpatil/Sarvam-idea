"""Gazetteer and Landmark Spatial Index for Signal Fusion Board.

Focus District: Patna Inundation & Ganga Basin Emergency Zone
Provides:
- Seeded OSM landmark nodes with lat/lng
- Script-to-Latin transliteration & alias mapping (Devanagari, Bengali, English)
- Fuzzy gazetteer matching for Tier-2 geo-resolution
- Relative spatial offset calculations for Tier-3 landmark constraints
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

# District Center: Patna, Bihar (approx 25.6100° N, 85.1415° E)
DISTRICT_BOUNDS = {
    "name": "Patna Flood Basin",
    "state": "Bihar",
    "center": [25.6100, 85.1415],
    "lat_min": 25.5500,
    "lat_max": 25.6600,
    "lng_min": 85.0500,
    "lng_max": 85.2500
}

# Curated High-Fidelity OSM Landmarks with multilingual aliases
LANDMARKS = [
    {
        "id": "lm-digha-ghat",
        "name": "Digha Ghat",
        "aliases": ["दीघा घाट", "দীঘা ঘাট", "digha ghat", "digha bridge", "jp ganga path digha"],
        "category": "River Embankment & Bridge",
        "lat": 25.6425,
        "lng": 85.1012,
        "base_uncertainty_m": 150
    },
    {
        "id": "lm-rajendra-nagar-culvert",
        "name": "Rajendra Nagar Culvert",
        "aliases": ["राजेन्द्र नगर पुलिया", "राजेन्द्र नगर", "rajendra nagar", "rajendra nagar nala", "bazar samiti road"],
        "category": "Low-Lying Urban Drain / Culvert",
        "lat": 25.5992,
        "lng": 85.1610,
        "base_uncertainty_m": 200
    },
    {
        "id": "lm-kankarbagh-colony",
        "name": "Kankarbagh Colony Sector 3",
        "aliases": ["कंकड़बाग", "कंकड़बाग सेक्टर 3", "kankarbagh", "kankarbagh tempo stand", "tiwari bechar"],
        "category": "Dense Residential Sector",
        "lat": 25.5895,
        "lng": 85.1485,
        "base_uncertainty_m": 250
    },
    {
        "id": "lm-mg-setu-zero-mile",
        "name": "MG Setu Zero Mile",
        "aliases": ["गांधी सेतु जीरो माइल", "महात्मा गांधी सेतु", "mg setu", "zero mile pahari", "zero mile"],
        "category": "National Highway & River Crossroad",
        "lat": 25.5780,
        "lng": 85.2050,
        "base_uncertainty_m": 300
    },
    {
        "id": "lm-danapur-cantt-bridge",
        "name": "Danapur Cantonment Old Bridge",
        "aliases": ["दानापुर छावनी", "दानापुर पुराना पुल", "danapur cantt", "danapur station road", "takiyapar"],
        "category": "Army Cantonment & Sone Channel",
        "lat": 25.6285,
        "lng": 85.0450,
        "base_uncertainty_m": 200
    },
    {
        "id": "lm-boring-canal-substation",
        "name": "Boring Canal Road Substation",
        "aliases": ["बोरिंग कैनाल रोड", "विद्युत सबस्टेशन", "boring road", "boring canal", "anandpuri"],
        "category": "Critical Power Infrastructure",
        "lat": 25.6180,
        "lng": 85.1210,
        "base_uncertainty_m": 120
    },
    {
        "id": "lm-gai-ghat-riverfront",
        "name": "Gai Ghat Riverfront",
        "aliases": ["गाय घाट", "गायघाट स्लम", "gai ghat", "bhadra ghat", "patna city ghat"],
        "category": "Informal Riverbank Settlement",
        "lat": 25.6080,
        "lng": 85.1880,
        "base_uncertainty_m": 180
    },
    {
        "id": "lm-pmch-emergency-gate",
        "name": "PMCH Hospital Emergency Gate",
        "aliases": ["पीएमसीएच", "पटना मेडिकल कॉलेज", "pmch", "ashok rajpath pmch", "patna medical college"],
        "category": "Tertiary Care Hospital",
        "lat": 25.6215,
        "lng": 85.1585,
        "base_uncertainty_m": 100
    },
    {
        "id": "lm-patna-junction-south",
        "name": "Patna Junction South Terminal",
        "aliases": ["पटना जंक्शन", "karbigahiya", "करबिगहिया", "patna junction", "chiraiyatand flyover"],
        "category": "Major Railway Transit",
        "lat": 25.5975,
        "lng": 85.1370,
        "base_uncertainty_m": 150
    },
    {
        "id": "lm-sabzibagh-market",
        "name": "Sabzibagh Market Alley",
        "aliases": ["सब्जीबाग", "sabzibagh", "machhua toli", "musallahpur"],
        "category": "High-Density Commercial Slum",
        "lat": 25.6135,
        "lng": 85.1510,
        "base_uncertainty_m": 180
    }
]


# Simple Indic-to-Latin phonetic character replacements
TRANSLITERATION_MAP = {
    "घाट": "ghat", "पुल": "pul", "पुलिया": "puliya", "रोड": "road", "नगर": "nagar",
    "बाग": "bagh", "थाना": "thana", "अस्पताल": "hospital", "मार्केट": "market", "गली": "gali"
}


def normalize_text(text: str) -> str:
    """Normalize text across Hindi/Bengali/English for fuzzy lookup."""
    low = text.lower().strip()
    for indic_w, eng_w in TRANSLITERATION_MAP.items():
        low = low.replace(indic_w, eng_w)
    # Remove excessive punctuation
    return re.sub(r"[^\w\s]", " ", low)


def match_landmark(text_mention: str) -> Optional[Dict[str, Any]]:
    """Tier-2 Gazetteer Lookup: Match landmark by name or alias."""
    norm = normalize_text(text_mention)
    best_match = None
    best_score = 0

    for lm in LANDMARKS:
        # Check canonical name and direct aliases
        candidate_names = [lm["name"]] + lm.get("aliases", [])
        for alias in candidate_names:
            alias_norm = normalize_text(alias)
            if alias_norm in norm or norm in alias_norm:
                score = len(alias_norm) / max(len(norm), 1)
                if score > best_score:
                    best_score = score
                    best_match = lm

    return best_match


def calculate_offset(lat: float, lng: float, bearing_deg: float, distance_m: float) -> Tuple[float, float]:
    """Calculate target lat/lng given starting point, bearing, and distance."""
    earth_radius_m = 6371000.0
    d_div_r = distance_m / earth_radius_m
    rad_bearing = math.radians(bearing_deg)

    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)

    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(d_div_r) +
        math.cos(lat_rad) * math.sin(d_div_r) * math.cos(rad_bearing)
    )

    new_lng_rad = lng_rad + math.atan2(
        math.sin(rad_bearing) * math.sin(d_div_r) * math.cos(lat_rad),
        math.cos(d_div_r) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )

    return (math.degrees(new_lat_rad), math.degrees(new_lng_rad))


def parse_relative_direction(direction_str: str) -> float:
    """Map compass and relative mentions to degrees."""
    d = direction_str.lower()
    if "north" in d or "उत्तर" in d or "up" in d:
        return 0.0
    if "east" in d or "पूर्व" in d or "purab" in d:
        return 90.0
    if "south" in d or "दक्षिण" in d or "down" in d:
        return 180.0
    if "west" in d or "पश्चिम" in d:
        return 270.0
    if "behind" in d or "पीछे" in d:
        return 225.0
    if "front" in d or "सामने" in d:
        return 45.0
    return 90.0  # default
