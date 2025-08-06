import json
import os
from datetime import datetime
from data_process import get_processed_news_data
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File paths
template_path = "utils/templates/template_placeholder.html"
output_path = "utils/templates/template_today.html"
outputs_dir = "outputs"

# Load JSON data from data_process function
def load_json_from_api(api_key: str = None):
    processed_data = get_processed_news_data(api_key)
    return json.loads(processed_data)

# Load HTML template
def load_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# Fill placeholders in template
def fill_template(template, data):
    # Past 24 hours
    for i in range(1, 7):
        key = f"24h_{i}"
        value = data["past_24_hours"].get(key, "")
        template = template.replace(f"{{{key}}}", value)
    # Viral
    for i in range(1, 4):
        key = f"viral_{i}"
        value = data["whats_going_viral"].get(key, "")
        template = template.replace(f"{{{key}}}", value)
    # Company developments
    company_dev = data["innovations_and_developments"].get("company_developments", "")
    template = template.replace("{company_developments}", company_dev)
    return template

# Save filled template
def save_output(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_copy_to_outputs(content):
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
    today = datetime.now()
    date_str = today.strftime("%d_%m_%Y")
    # Find next available N for today
    existing = [fname for fname in os.listdir(outputs_dir) if fname.startswith(f"template_today__number_") and fname.endswith(f"_{date_str}.html")]
    N = 1
    if existing:
        nums = []
        for fname in existing:
            try:
                num_part = fname.split("__number_")[1].split("_")[0]
                nums.append(int(num_part))
            except Exception:
                continue
        if nums:
            N = max(nums) + 1
    output_filename = f"template_today__number_{N}_{date_str}.html"
    output_path_full = os.path.join(outputs_dir, output_filename)
    with open(output_path_full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved copy: {output_path_full}")

def main():
    # Get data from API and process it (uses API key from .env file)
    data = load_json_from_api()
    template = load_template(template_path)
    filled = fill_template(template, data)
    save_output(output_path, filled)
    save_copy_to_outputs(filled)

if __name__ == "__main__":
    main()
