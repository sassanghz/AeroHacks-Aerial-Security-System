from google import genai
from google.genai import types
import json
import re

with open('test.jpg', 'rb') as f:
      image_bytes = f.read()

client = genai.Client(api_key="API_KEY")

imagePrompt = """You are a JSON-only response generator. Analyze the provided image and return plain text containing only one JSON object. No markdown, no explanation, no extra keys.

        Return exactly this structure:

        {
        "age": "string",
        "skin_tone": "string",
        "facial_features": ["string"],
        "clothing": ["string"],
        "injuries_or_condition": ["string"],
        "uncertainty": ["string"]
        }

        Rules:
        - Report only directly visible details.
        - Keep all text minimal, specific, and neutral.
        - Use short phrases only, not sentences, unless absolutely necessary.
        - Do not guess identity, ethnicity, intent, occupation, or cause of injuries.
        - Give approximate age range only if visually supported; otherwise use "Not clearly visible".
        - For skin tone, describe only visible complexion in simple neutral terms; if unclear, use "Not clearly visible".
        - For injuries or condition, describe only visible non-graphic signs such as bruise, swelling, cut, abrasion, blood, bandage, torn clothing, or abnormal posture.
        - If a category has no clear evidence, return either:
        - "Not clearly visible" for string fields
        - ["None visible"] or ["Not clearly visible"] for array fields, whichever fits better
        - Do not mention image areas.
        - Do not include background, surroundings, identity clues, or extra narrative.
        - Output must be valid JSON.

        Field guidance:
        - "age": short approximate range only, e.g. "20-30", or "Not clearly visible"
        - "skin_tone": short visible descriptor only, e.g. "light", "medium", "dark", "brown", or "Not clearly visible"
        - "facial_features": only key visible traits useful for description, e.g. ["oval face", "thick eyebrows", "short beard"]
        - "clothing": only visible clothing items/colors, e.g. ["black hoodie", "blue jeans"]
        - "injuries_or_condition": only visible cuts/injuries/physical condition, e.g. ["small cut on cheek", "swelling under left eye"] or ["None visible"]
        - "uncertainty": short limits only, e.g. ["face partially obscured", "low resolution"]

        Do not output anything else."""

def analyzeImage(imagePath):
    with open(imagePath, 'rb') as f:
      image = f.read()

    response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents=[
        types.Part.from_bytes(
        data=image,
        mime_type='image/jpeg',
        ),
        imagePrompt
        ]
    )
    saveAnalysis(response.text)
    return response.text

def saveAnalysis(analysis):
    try:
        parsed = json.loads(analysis)
        with open("analysis.json", "w") as f:
                json.dump(parsed, f, indent=2)
        return "JSON extracted and saved."

    except json.JSONDecodeError:
        pass

    match = re.search(r"```json\s*(\{.*?\})\s*```", analysis, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            parsed = json.loads(json_str)
            with open("analysis.json", "w") as f:
                json.dump(parsed, f, indent=2)
            return "JSON extracted and saved."
        except json.JSONDecodeError:
            return "JSON block found but couldn't parse it."
    else:
        return "No JSON block found in the response."

print(analyzeImage('test.jpg'))