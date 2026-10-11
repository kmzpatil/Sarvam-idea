"""Pre-approved Safety Advisory Templates and Bulbul Audio Dispatch.

Safety Optic: 105B selects approved templates only — never hallucinates safety instructions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from backend.sarvam_client import SarvamClient

# Standard NDMA (National Disaster Management Authority) Aligned Templates
PRE_APPROVED_TEMPLATES = {
    "flood_rising_water": {
        "id": "tpl_flood_rising",
        "title": "Rising Floodwater Immediate Protocol",
        "hi-IN": "आपातकालीन सलाह: तुरंत सबसे ऊपरी मंजिल या पक्की छत पर जाएं। बहते पानी में न उतरें और बिजली के खंभों से दूर रहें। एनडीआरएफ बचाव दल को आपके स्थान की सूचना दे दी गई है।",
        "bn-IN": "জরুরী পরামর্শ: অবিলম্বে সবচেয়ে উঁচু তলা বা পাকা ছাদে যান। প্রবাহিত জলে নামবেন না। বিদ্যুতের তার স্পর্শ করবেন না। উদ্ধারকারী দল আপনার লোকেশনে রওনা হয়েছে।",
        "en-IN": "Emergency Advisory: Move immediately to the highest floor or nearest pucca roof. Avoid moving floodwaters and stay clear of submerged cables. Rescue teams have been alerted."
    },
    "embankment_breach": {
        "id": "tpl_embankment_breach",
        "title": "Embankment Breach Evacuation",
        "hi-IN": "सावधान: तटबंध टूटने की सूचना मिली है। जलस्तर तेजी से बढ़ रहा है। तुरंत ऊंचे रिलीफ कैंप की ओर प्रस्थान करें। आवश्यक दवाएं और पहचान पत्र साथ रखें।",
        "bn-IN": "সতর্কতা: বাঁধ ভাঙার খবর পাওয়া গেছে। দ্রুত উঁচু ত্রাণ শিবিরের দিকে যান। প্রয়োজনীয় ওষুধ এবং নথিপত্র সঙ্গে রাখুন।",
        "en-IN": "Urgent Advisory: River embankment breach reported. Evacuate immediately towards designated high-ground relief centers. Carry essential medicines and ID proofs."
    },
    "medical_emergency": {
        "id": "tpl_medical_emergency",
        "title": "Critical Medical Evacuation",
        "hi-IN": "चिकित्सा सहायता संदेश: मरीज को सूखे व सुरक्षित स्थान पर रखें। मेडिकल बोट रवाना हो चुकी है। बचाव दल के पहुंचने पर टॉर्च या सफेद कपड़ा लहराएं।",
        "bn-IN": "চিকিৎসা সহায়তা বার্তা: রোগীকে শুকনো ও নিরাপদ স্থানে রাখুন। মেডিকেল বোট পাঠানো হয়েছে। উদ্ধারকারী দল এলে টর্চ বা সাদা কাপড় দোলাবেন।",
        "en-IN": "Medical Rescue Notice: Keep patient sheltered on elevated dry ground. Emergency medical transport boat deployed. Flash torch or wave cloth when rescue team approaches."
    }
}


def get_advisory_for_hazard(hazard_type: str, language_code: str = "hi-IN") -> Dict[str, str]:
    """Select the pre-approved template matching hazard classification."""
    hz_lower = hazard_type.lower()
    if "medical" in hz_lower or "patient" in hz_lower or "hospital" in hz_lower:
        tpl_key = "medical_emergency"
    elif "breach" in hz_lower or "collapse" in hz_lower or "dam" in hz_lower:
        tpl_key = "embankment_breach"
    else:
        tpl_key = "flood_rising_water"

    tpl = PRE_APPROVED_TEMPLATES[tpl_key]
    script = tpl.get(language_code, tpl["hi-IN"])

    return {
        "template_id": tpl["id"],
        "template_title": tpl["title"],
        "language_code": language_code,
        "advisory_text": script
    }


def synthesize_advisory_audio(client: SarvamClient, hazard_type: str, language_code: str = "hi-IN") -> Dict[str, Any]:
    """Generate verified audio advisory via Bulbul v3."""
    advisory_data = get_advisory_for_hazard(hazard_type, language_code)
    text = advisory_data["advisory_text"]
    
    tts_result = client.text_to_speech(text, target_language_code=language_code)
    
    return {
        **advisory_data,
        "audio_base64": tts_result.get("audio_base64") if tts_result.get("success") else None,
        "speaker": tts_result.get("speaker", "priya"),
        "success": tts_result.get("success", False)
    }
