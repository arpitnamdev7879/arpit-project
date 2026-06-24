from agents.jd_analyzer import analyze_jd
from agents.github_audit import audit_github
from agents.fraud_detector import compute_fraud_score
from agents.scoring import compute_scores
from agents.explainability import generate_explanation, generate_interview_questions
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)


def run_pipeline_for_candidate(username: str, jd_data: dict) -> dict:
    """Run the full analysis pipeline for a single candidate."""
    print(f"  [GitHub Audit] Auditing @{username}...")
    github_data = audit_github(username)

    if "error" in github_data:
        return {"username": username, "error": github_data["error"]}

    print(f"  [Fraud Detector] Checking @{username}...")
    fraud_result = compute_fraud_score(github_data)

    print(f"  [Scoring] Computing scores for @{username}...")
    scores = compute_scores(github_data, jd_data, fraud_result)

    print(f"  [Explainability] Generating report for @{username}...")
    explanation = generate_explanation(github_data, scores, jd_data, fraud_result)

    print(f"  [Interview Gen] Generating questions for @{username}...")
    interview_questions = generate_interview_questions(github_data, scores, jd_data)

    return {
        "github_data": github_data,
        "fraud_result": fraud_result,
        "scores": scores,
        "explanation": explanation,
        "interview_questions": interview_questions,
    }


def run_full_pipeline(jd_text: str, github_usernames: list[str]) -> dict:
    """Orchestrate the full TalentGPT pipeline."""
    print("[Orchestrator] Starting TalentGPT pipeline...")

    print("[JD Analyzer] Analyzing job description...")
    jd_data = analyze_jd(jd_text)
    print(f"  Extracted {len(jd_data.get('must_have_skills', []))} required skills")

    results = []
    for username in github_usernames:
        print(f"[Pipeline] Processing candidate: @{username}")
        result = run_pipeline_for_candidate(username.strip(), jd_data)
        results.append(result)

    # Filter errors
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    # Rank by total score
    valid.sort(key=lambda x: x["scores"]["total_score"], reverse=True)
    for i, r in enumerate(valid):
        r["rank"] = i + 1

    print(f"[Orchestrator] Pipeline complete. {len(valid)} candidates analyzed.")
    return {
        "jd_data": jd_data,
        "candidates": valid,
        "errors": errors,
        "total_processed": len(results),
    }
