import json
import sys
import os
from typing import Any, Dict
from data_query import fetch_tech_news
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load the response template to get the required structure
with open('utils/templates/response_template.json', 'r', encoding='utf-8') as f:
    template = json.load(f)

def validate_and_correct(response: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively ensure response matches the template structure.
    Fill missing keys with template values.
    """
    corrected = {}
    for key, value in template.items():
        if key in response:
            if isinstance(value, dict) and isinstance(response[key], dict):
                corrected[key] = validate_and_correct(response[key], value)
            else:
                corrected[key] = response[key]
        else:
            corrected[key] = value
    return corrected

def is_matching(response: Dict[str, Any], template: Dict[str, Any]) -> bool:
    """
    Check if response matches the template structure (all keys, types, and nesting).
    """
    for key, value in template.items():
        if key not in response:
            return False
        if isinstance(value, dict):
            if not isinstance(response[key], dict):
                return False
            if not is_matching(response[key], value):
                return False
    return True

def process_response(response_data: str) -> str:
    try:
        response = json.loads(response_data)
    except json.JSONDecodeError as e:
        # If not valid JSON, return template as fallback
        return json.dumps(template, ensure_ascii=False, indent=2)
    if is_matching(response, template):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        corrected = validate_and_correct(response, template)
        return json.dumps(corrected, ensure_ascii=False, indent=2)

def process_api_response(api_key: str = None) -> str:
    """Fetch data from API and process it directly"""
    # Fetch data from API
    news_data = fetch_tech_news(api_key)
    
    if news_data is None:
        print("Failed to fetch data from API")
        return json.dumps(template, ensure_ascii=False, indent=2)
    
    # Convert Pydantic model to dict with aliases
    response_dict = news_data.model_dump(by_alias=True)
    
    # Process the response
    return process_response(json.dumps(response_dict))

def get_processed_news_data(api_key: str = None) -> str:
    """
    Main function to fetch and process news data.
    
    Args:
        api_key: Your Perplexity API key (optional, will use env var if not provided)
        
    Returns:
        str: Processed JSON data as a string
    """
    # Process API response directly
    output = process_api_response(api_key)
    return output
