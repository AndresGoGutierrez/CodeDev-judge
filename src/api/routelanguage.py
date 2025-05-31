from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from src.core.config import settings

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_languages():
    """
    Get the list of supported programming languages.
    """
    languages = []
    
    # Mapping of IDs to language names
    language_names = {
        50: "C (GCC 9.2.0)",
        51: "C# (Mono 6.6.0.161)",
        54: "C++ (GCC 9.2.0)",
        60: "Go (1.13.5)",
        62: "Java (OpenJDK 13.0.1)",
        63: "JavaScript (Node.js 12.14.0)",
        71: "Python 3.8",
        72: "Ruby (2.7.0)",
        73: "Rust (1.40.0)"
    }
    
    # Get the languages configured in settings.LANGUAGE_MAP
    for internal_id, judge0_id in settings.LANGUAGE_MAP.items():
        # Only include internal IDs (1-9) to avoid duplicates
        if 1 <= internal_id <= 9:
            name = language_names.get(judge0_id, f"Language ID {judge0_id}")
            languages.append({
                "id": internal_id,
                "name": name
            })
    
    return languages
