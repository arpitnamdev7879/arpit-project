from google import genai
import json
import re
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_explanation(github_data: dict, scores: dict, jd_data: dict, fraud_result: dict) -> str:
    """Generate human-readable XAI explanation for candidate scores."""
    repos = github_data.get("repos", [])
    top_repos_summary = "\n".join([
        f"- {r['name']} ({r['language']}): {r['commits']} commits, {r['stars']} stars, README: {r['has_readme']}"
        for r in repos[:4]
    ])

    fraud_signals_text = "\n".join([
        f"- {s['type']}: {s['detail']}" for s in fraud_result.get("signals", [])
    ]) or "None detected"

    prompt = f"""
You are a senior technical recruiter writing a candidate evaluation report.

Candidate: {github_data.get('name', github_data.get('username'))}
GitHub: @{github_data.get('username')}

SCORES:
- Technical Execution: {scores['technical_score']}/100
- Code Quality: {scores['code_quality_score']}/100
- Learning Velocity: {scores['learning_velocity_score']}/100
- Collaboration: {scores['collaboration_score']}/100
- Skill Alignment: {scores['skill_alignment_score']}/100
- TOTAL: {scores['total_score']}/100

TOP REPOSITORIES:
{top_repos_summary}

FRAUD FLAGS: {fraud_result.get('risk_level')} risk
{fraud_signals_text}

SKILL GAPS: {', '.join(scores.get('skill_gaps', [])) or 'None'}
JOB REQUIREMENTS: {', '.join(jd_data.get('must_have_skills', []))}

Write a 3-4 sentence professional evaluation explaining:
1. Why this candidate scored the way they did (link to specific repos/commits)
2. Key strengths with evidence
3. Areas of concern or skill gaps
4. Overall recommendation (Strong Yes / Yes / Maybe / No)

Be specific, evidence-based, and professional. Do NOT use markdown formatting.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return (
            f"Candidate {github_data.get('username')} scored {scores['total_score']}/100. "
            f"Analysis based on {github_data.get('total_commits', 0)} commits across "
            f"{len(repos)} repositories. Fraud risk: {fraud_result.get('risk_level')}."
        )


def generate_interview_questions(github_data: dict, scores: dict, jd_data: dict) -> list:
    """Generate personalized interview questions."""
    repos = github_data.get("repos", [])
    top_repo = repos[0] if repos else {}
    skill_gaps = scores.get("skill_gaps", [])

    prompt = f"""
Generate 8 personalized interview questions for this candidate.

Candidate GitHub: @{github_data.get('username')}
Role: {jd_data.get('title', 'Software Engineer')} ({jd_data.get('seniority', 'mid')})
Top Project: {top_repo.get('name', 'N/A')} — {top_repo.get('description', '')}
Languages: {', '.join(list(github_data.get('languages', {}).keys())[:5])}
Skill Gaps: {', '.join(skill_gaps) or 'None'}

Return a JSON array of 8 question objects, no markdown:
[
  {{"type": "project", "question": "...", "follow_up": "..."}},
  {{"type": "technical", "question": "...", "follow_up": "..."}},
  {{"type": "skill_gap", "question": "...", "follow_up": "..."}},
  {{"type": "behavioral", "question": "...", "follow_up": "..."}}
]

Make questions specific to their actual work. Include 2 project questions, 3 technical, 2 skill-gap, 1 behavioral.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception as e:
        return [
            {"type": "technical", "question": f"Walk me through your most complex project on GitHub.", "follow_up": "What challenges did you face?"},
            {"type": "behavioral", "question": "Describe a time you had to learn a new technology quickly.", "follow_up": "How did you approach it?"},
        ]
