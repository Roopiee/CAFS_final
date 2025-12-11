from app.agents.ext import ExtractionAgent
import json

# Initialize the agent with your Mistral AI API key
agent = ExtractionAgent(api_key="nJpjawyHlBoqUrTBSxtOE2oA2KytRL2Y")

# Path to the image to extract text from
image_path = "jpgconvertedimgs/fakecft/fakecft_page-0001.jpg"

# Read image bytes
with open(image_path, "rb") as f:
    image_bytes = f.read()

# Extract data using the agent
result = agent.extract(image_bytes)

# Pretty-print the result
print(json.dumps(result, indent=2))
