import json
import sys
import os
import requests
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging():
    """Configure comprehensive logging for the application"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logging
    log_filename = f"logs/newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger for this application
    logger = logging.getLogger('NewsletterGenerator')
    logger.setLevel(logging.DEBUG)
    
    logger.info(f"Logging initialized. Log file: {log_filename}")
    return logger

# Initialize logger
logger = setup_logging()

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# ============================================================================
# DATA QUERY SECTION (from data_query.py)
# ============================================================================

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
    logger.info("Starting API data fetch process")
    
    try:
        # Use API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('PERPLEXITY_API_KEY')
            logger.debug(f"API key from environment: {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'None'}")
            if not api_key:
                error_msg = "PERPLEXITY_API_KEY not found in environment variables"
                logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            logger.debug(f"API key provided directly: {'*' * (len(api_key) - 4) + api_key[-4:]}")
        
        # Read the prompt from pplx_prompt.txt
        prompt_path = 'utils/templates/pplx_prompt.txt'
        logger.debug(f"Reading prompt from: {prompt_path}")
        
        if not os.path.exists(prompt_path):
            error_msg = f"Prompt file not found: {prompt_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        logger.debug(f"Prompt loaded successfully. Length: {len(prompt)} characters")
        logger.debug(f"Prompt preview: {prompt[:200]}...")

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
        
        logger.info(f"Making API request to: {url}")
        logger.debug(f"Request payload keys: {list(payload.keys())}")
        logger.debug(f"Model: {payload['model']}")
        logger.debug(f"Response format: {payload['response_format']}")

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        logger.info(f"API response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Response data keys: {list(data.keys())}")
            
            try:
                news_data = TechNewsResponse.model_validate_json(
                    data["choices"][0]["message"]["content"]
                )
                logger.info("Successfully parsed API response into TechNewsResponse model")
                
                # Print the structured data
                print("=== Past 24 Hours ===")
                for i, (key, value) in enumerate(news_data.past_24_hours.model_dump().items(), 1):
                    print(f"{i}. {value}")
                    logger.debug(f"24h_{i}: {value[:100]}...")
                
                print("\n=== What's Going Viral ===")
                for i, (key, value) in enumerate(news_data.whats_going_viral.model_dump().items(), 1):
                    print(f"{i}. {value}")
                    logger.debug(f"viral_{i}: {value[:100]}...")
                
                print("\n=== Innovations & Developments ===")
                print(news_data.innovations_and_developments.company_developments)
                logger.debug(f"company_developments: {news_data.innovations_and_developments.company_developments[:100]}...")
                
                # Return the structured data
                logger.info("API data fetch completed successfully")
                return news_data
                
            except Exception as e:
                logger.error(f"Failed to parse API response: {e}")
                logger.debug(f"Raw response content: {data}")
                raise
                
        else:
            error_msg = f'API Error: {response.status_code} - {response.text}'
            logger.error(error_msg)
            logger.debug(f"Full response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        error_msg = "API request timed out after 60 seconds"
        logger.error(error_msg)
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during API request: {e}"
        logger.error(error_msg)
        return None
    except Exception as e:
        error_msg = f"Unexpected error during API fetch: {e}"
        logger.error(error_msg)
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        return None

# ============================================================================
# DATA PROCESS SECTION (from data_process.py)
# ============================================================================

# Load the response template to get the required structure
template_path = 'utils/templates/response_template.json'
logger.info(f"Loading response template from: {template_path}")

try:
    if not os.path.exists(template_path):
        error_msg = f"Template file not found: {template_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    logger.info("Response template loaded successfully")
    logger.debug(f"Template keys: {list(template.keys())}")
except Exception as e:
    logger.error(f"Failed to load response template: {e}")
    template = {}

def validate_and_correct(response: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively ensure response matches the template structure.
    Fill missing keys with template values.
    """
    logger.debug("Starting response validation and correction")
    corrected = {}
    for key, value in template.items():
        if key in response:
            if isinstance(value, dict) and isinstance(response[key], dict):
                logger.debug(f"Recursively validating nested dict for key: {key}")
                corrected[key] = validate_and_correct(response[key], value)
            else:
                logger.debug(f"Using existing value for key: {key}")
                corrected[key] = response[key]
        else:
            logger.debug(f"Using template value for missing key: {key}")
            corrected[key] = value
    return corrected

def is_matching(response: Dict[str, Any], template: Dict[str, Any]) -> bool:
    """
    Check if response matches the template structure (all keys, types, and nesting).
    """
    logger.debug("Checking if response matches template structure")
    for key, value in template.items():
        if key not in response:
            logger.debug(f"Missing key in response: {key}")
            return False
        if isinstance(value, dict):
            if not isinstance(response[key], dict):
                logger.debug(f"Expected dict for key {key}, got {type(response[key])}")
                return False
            if not is_matching(response[key], value):
                logger.debug(f"Nested structure mismatch for key: {key}")
                return False
    logger.debug("Response structure matches template")
    return True

def process_response(response_data: str) -> str:
    logger.info("Processing API response data")
    logger.debug(f"Input data length: {len(response_data)} characters")
    
    try:
        response = json.loads(response_data)
        logger.debug("Successfully parsed JSON response")
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in response: {e}"
        logger.error(error_msg)
        logger.debug(f"Raw response data: {response_data[:500]}...")
        # If not valid JSON, return template as fallback
        fallback = json.dumps(template, ensure_ascii=False, indent=2)
        logger.info("Using template as fallback due to JSON decode error")
        return fallback
    
    if is_matching(response, template):
        logger.info("Response matches template structure exactly")
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        logger.info("Response structure corrected to match template")
        corrected = validate_and_correct(response, template)
        return json.dumps(corrected, ensure_ascii=False, indent=2)

def process_api_response(api_key: str = None) -> str:
    """Fetch data from API and process it directly"""
    logger.info("Starting API response processing")
    
    # Fetch data from API
    news_data = fetch_tech_news(api_key)
    
    if news_data is None:
        error_msg = "Failed to fetch data from API"
        logger.error(error_msg)
        fallback = json.dumps(template, ensure_ascii=False, indent=2)
        logger.info("Using template as fallback due to API failure")
        return fallback
    
    # Convert Pydantic model to dict with aliases
    try:
        response_dict = news_data.model_dump(by_alias=True)
        logger.debug("Successfully converted Pydantic model to dict")
        logger.debug(f"Response dict keys: {list(response_dict.keys())}")
    except Exception as e:
        error_msg = f"Failed to convert Pydantic model to dict: {e}"
        logger.error(error_msg)
        fallback = json.dumps(template, ensure_ascii=False, indent=2)
        logger.info("Using template as fallback due to model conversion error")
        return fallback
    
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
    logger.info("Starting news data processing pipeline")
    # Process API response directly
    output = process_api_response(api_key)
    logger.info("News data processing completed")
    logger.debug(f"Output data length: {len(output)} characters")
    return output

# ============================================================================
# NEWSLETTER SECTION (from newsletter.py)
# ============================================================================

# File paths
template_path = "utils/templates/template_placeholder.html"
output_path = "utils/templates/template_today.html"
outputs_dir = "outputs"

logger.info(f"Template path: {template_path}")
logger.info(f"Output path: {output_path}")
logger.info(f"Outputs directory: {outputs_dir}")

# Load JSON data from data_process function
def load_json_from_api(api_key: str = None):
    logger.info("Loading JSON data from API")
    processed_data = get_processed_news_data(api_key)
    
    try:
        data = json.loads(processed_data)
        logger.info("Successfully parsed processed data as JSON")
        logger.debug(f"Data keys: {list(data.keys())}")
        return data
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse processed data as JSON: {e}"
        logger.error(error_msg)
        logger.debug(f"Raw processed data: {processed_data[:500]}...")
        raise

# Load HTML template
def load_template(path):
    logger.info(f"Loading HTML template from: {path}")
    
    if not os.path.exists(path):
        error_msg = f"Template file not found: {path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        logger.info(f"Template loaded successfully. Length: {len(template_content)} characters")
        logger.debug(f"Template preview: {template_content[:200]}...")
        return template_content
    except Exception as e:
        error_msg = f"Failed to load template: {e}"
        logger.error(error_msg)
        raise

# Fill placeholders in template
def fill_template(template, data):
    logger.info("Starting template placeholder replacement")
    original_template = template
    
    try:
        # Past 24 hours
        logger.debug("Processing past 24 hours placeholders")
        for i in range(1, 7):
            key = f"24h_{i}"
            value = data["past_24_hours"].get(key, "")
            logger.debug(f"Replacing {key} with: {value[:50]}...")
            template = template.replace(f"{{{key}}}", value)
        
        # Viral
        logger.debug("Processing viral placeholders")
        for i in range(1, 4):
            key = f"viral_{i}"
            value = data["whats_going_viral"].get(key, "")
            logger.debug(f"Replacing {key} with: {value[:50]}...")
            template = template.replace(f"{{{key}}}", value)
        
        # Company developments
        logger.debug("Processing company developments placeholder")
        company_dev = data["innovations_and_developments"].get("company_developments", "")
        logger.debug(f"Replacing company_developments with: {company_dev[:50]}...")
        template = template.replace("{company_developments}", company_dev)
        
        logger.info("Template placeholder replacement completed")
        logger.debug(f"Template length before: {len(original_template)}, after: {len(template)}")
        return template
        
    except Exception as e:
        error_msg = f"Error during template filling: {e}"
        logger.error(error_msg)
        logger.debug(f"Data structure: {data}")
        raise

# Save filled template
def save_output(path, content):
    logger.info(f"Saving filled template to: {path}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Template saved successfully. Size: {len(content)} characters")
    except Exception as e:
        error_msg = f"Failed to save template: {e}"
        logger.error(error_msg)
        raise

def save_copy_to_outputs(content):
    logger.info("Saving copy to outputs directory")
    
    try:
        if not os.path.exists(outputs_dir):
            logger.info(f"Creating outputs directory: {outputs_dir}")
            os.makedirs(outputs_dir)
        
        today = datetime.now()
        date_str = today.strftime("%d_%m_%Y")
        logger.debug(f"Date string: {date_str}")
        
        # Find next available N for today
        existing = [fname for fname in os.listdir(outputs_dir) if fname.startswith(f"template_today__number_") and fname.endswith(f"_{date_str}.html")]
        logger.debug(f"Existing files for today: {existing}")
        
        N = 1
        if existing:
            nums = []
            for fname in existing:
                try:
                    num_part = fname.split("__number_")[1].split("_")[0]
                    nums.append(int(num_part))
                except Exception as e:
                    logger.warning(f"Could not parse number from filename {fname}: {e}")
                    continue
            if nums:
                N = max(nums) + 1
                logger.debug(f"Next available number: {N}")
        
        output_filename = f"template_today__number_{N}_{date_str}.html"
        output_path_full = os.path.join(outputs_dir, output_filename)
        
        logger.info(f"Saving to: {output_path_full}")
        with open(output_path_full, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Copy saved successfully: {output_path_full}")
        print(f"Saved copy: {output_path_full}")
        
    except Exception as e:
        error_msg = f"Failed to save copy to outputs: {e}"
        logger.error(error_msg)
        raise

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function that orchestrates the entire newsletter generation process"""
    logger.info("=" * 50)
    logger.info("STARTING NEWSLETTER GENERATION PROCESS")
    logger.info("=" * 50)
    
    start_time = datetime.now()
    logger.info(f"Process started at: {start_time}")
    
    try:
        # Get data from API and process it (uses API key from .env file)
        logger.info("Step 1: Loading JSON data from API")
        data = load_json_from_api()
        logger.info("✓ JSON data loaded successfully")
        
        # Load HTML template
        logger.info("Step 2: Loading HTML template")
        template = load_template(template_path)
        logger.info("✓ HTML template loaded successfully")
        
        # Fill template with data
        logger.info("Step 3: Filling template with data")
        filled = fill_template(template, data)
        logger.info("✓ Template filled successfully")
        
        # Save the filled template
        logger.info("Step 4: Saving filled template")
        save_output(output_path, filled)
        logger.info("✓ Template saved successfully")
        
        # Save copy to outputs directory
        logger.info("Step 5: Saving copy to outputs directory")
        save_copy_to_outputs(filled)
        logger.info("✓ Copy saved to outputs directory")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info("=" * 50)
        logger.info("NEWSLETTER GENERATION COMPLETED SUCCESSFULLY")
        logger.info(f"Process completed at: {end_time}")
        logger.info(f"Total duration: {duration}")
        logger.info("=" * 50)
        
        print("Newsletter generation completed successfully!")
        
    except FileNotFoundError as e:
        error_msg = f"File not found error: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
        
    except ValueError as e:
        error_msg = f"Configuration error: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network/API error: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"Unexpected error during newsletter generation: {e}"
        logger.error(error_msg)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"Error: {error_msg}")
        sys.exit(1)

if __name__ == "__main__":
    main()
