from google import genai
from google.genai import types
import json
import re
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_jd(jd_text: str) -> dict:
    """Extract structured requirements from a Job Description."""
    prompt = f"""
You are an expert technical recruiter. Analyze this Job Description and extract structured information.

JD:
{jd_text}

Return a JSON object with exactly this structure (no markdown, pure JSON):
{{
  "title": "Job title",
  "seniority": "junior|mid|senior|staff|principal",
  "domain": "backend|frontend|fullstack|ml|devops|data|mobile|other",
  "must_have_skills": ["skill1", "skill2"],
  "nice_to_have_skills": ["skill1", "skill2"],
  "experience_years": 3,
  "key_responsibilities": ["responsibility1", "responsibility2"],
  "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
  "skill_weights": {{
    "Python": 0.9,
    "FastAPI": 0.7
  }}
}}
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        # Extract JSON if wrapped in code blocks
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception as e:
        print(f"JD Analyzer error: {e}")
        return {
            "title": "Software Engineer",
            "seniority": "mid",
            "domain": "backend",
            "must_have_skills": ["Python"],
            "nice_to_have_skills": [],
            "experience_years": 2,
            "key_responsibilities": [],
            "tech_stack": ["Python"],
            "skill_weights": {"Python": 0.9}
        }
