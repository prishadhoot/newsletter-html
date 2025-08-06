import requests
import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Past24Hours(BaseModel):
    h24_1: str = Field(alias="24h_1")
    h24_2: str = Field(alias="24h_2")
    h24_3: str = Field(alias="24h_3")
    h24_4: str = Field(alias="24h_4")
    h24_5: str = Field(alias="24h_5")
    h24_6: str = Field(alias="24h_6")

class WhatsGoingViral(BaseModel):
    viral_1: str
    viral_2: str
    viral_3: str

class InnovationsAndDevelopments(BaseModel):
    company_developments: str

class TechNewsResponse(BaseModel):
    past_24_hours: Past24Hours
    whats_going_viral: WhatsGoingViral
    innovations_and_developments: InnovationsAndDevelopments

def fetch_tech_news(api_key: str = None) -> TechNewsResponse:
    """
    Fetch tech news from Perplexity API and return structured data.
    
    Args:
        api_key: Your Perplexity API key (optional, will use env var if not provided)
        
    Returns:
        TechNewsResponse: Structured news data
    """
    # Use API key from environment if not provided
    if api_key is None:
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    # Read the prompt from pplx_prompt.txt
    with open('utils/templates/pplx_prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()

    # Perplexity API configuration
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "model": "sonar",  # Using the model from your sample
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": TechNewsResponse.model_json_schema()
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            news_data = TechNewsResponse.model_validate_json(
                data["choices"][0]["message"]["content"]
            )
            
            # Print the structured data
            print("=== Past 24 Hours ===")
            for i, (key, value) in enumerate(news_data.past_24_hours.model_dump().items(), 1):
                print(f"{i}. {value}")
            
            print("\n=== What's Going Viral ===")
            for i, (key, value) in enumerate(news_data.whats_going_viral.model_dump().items(), 1):
                print(f"{i}. {value}")
            
            print("\n=== Innovations & Developments ===")
            print(news_data.innovations_and_developments.company_developments)
            
            # Return the structured data
            return news_data
            
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
            return None
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage (uncomment and add your API key)
if __name__ == "__main__":
    api_key = input("Enter your Perplexity API key: ")
    news_data = fetch_tech_news(api_key)
    if news_data:
        print("\nData fetched successfully!")
        print("You can now use data_process.py to process this data.")
