import math
from datetime import datetime, timezone


def compute_scores(github_data: dict, jd_data: dict, fraud_result: dict) -> dict:
    """Compute multi-dimensional candidate scores."""
    repos = github_data.get("repos", [])
    languages = github_data.get("languages", {})
    total_commits = github_data.get("total_commits", 0)
    followers = github_data.get("followers", 0)

    jd_skills = set(s.lower() for s in jd_data.get("must_have_skills", []) + jd_data.get("nice_to_have_skills", []))
    jd_tech = set(s.lower() for s in jd_data.get("tech_stack", []))

    # ── 1. Technical Execution (25%) ───────────────────────────────
    # Based on: working repos, commit volume, repo diversity
    non_empty_repos = [r for r in repos if r["commits"] > 5]
    has_tests = sum(1 for r in repos if r.get("has_tests", False))
    has_readme = sum(1 for r in repos if r.get("has_readme", False))

    tech_score = min(100,
        len(non_empty_repos) * 8 +
        min(total_commits, 1000) / 10 +
        has_tests * 5 +
        len(languages) * 3
    )

    # ── 2. Code Quality (20%) ──────────────────────────────────────
    # Based on: README presence, tests, repo descriptions
    described_repos = sum(1 for r in repos if len(r.get("description", "")) > 20)
    quality_score = min(100,
        (has_readme / max(len(repos), 1)) * 40 +
        (has_tests / max(len(repos), 1)) * 30 +
        (described_repos / max(len(repos), 1)) * 30
    )

    # ── 3. Learning Velocity (20%) ─────────────────────────────────
    # Based on: language diversity, recent activity
    try:
        created = datetime.fromisoformat(github_data.get("created_at", "2020-01-01").replace("Z", "+00:00"))
        account_age_years = max((datetime.now(timezone.utc) - created).days / 365, 0.5)
    except Exception:
        account_age_years = 2.0

    langs_per_year = len(languages) / account_age_years
    repos_per_year = len(repos) / account_age_years
    velocity_score = min(100, langs_per_year * 15 + repos_per_year * 5 + min(total_commits, 500) / 5)

    # ── 4. Collaboration (15%) ─────────────────────────────────────
    # Based on: followers, forked-by (stars approximate), public activity
    collab_score = min(100,
        math.log(followers + 1) * 15 +
        sum(r["forks"] for r in repos) * 2 +
        min(total_commits, 500) / 10
    )

    # ── 5. Skill Alignment (20%) ───────────────────────────────────
    candidate_langs = set(l.lower() for l in languages.keys())
    repo_langs = set()
    for r in repos:
        if r.get("language"):
            repo_langs.add(r["language"].lower())
        desc_words = r.get("description", "").lower().split()
        repo_langs.update(desc_words)

    all_candidate_skills = candidate_langs | repo_langs
    matched_skills = jd_skills & all_candidate_skills
    alignment_score = min(100, (len(matched_skills) / max(len(jd_skills), 1)) * 100) if jd_skills else 50.0

    # ── Weighted Total ─────────────────────────────────────────────
    weights = {
        "technical": 0.25,
        "code_quality": 0.20,
        "learning_velocity": 0.20,
        "collaboration": 0.15,
        "skill_alignment": 0.20
    }

    raw_total = (
        tech_score * weights["technical"] +
        quality_score * weights["code_quality"] +
        velocity_score * weights["learning_velocity"] +
        collab_score * weights["collaboration"] +
        alignment_score * weights["skill_alignment"]
    )

    # Fraud penalty (up to 30 points deducted)
    fraud_penalty = fraud_result.get("fraud_score", 0) * 30
    final_score = max(0, raw_total - fraud_penalty)

    # Skill gaps
    skill_gaps = list(jd_skills - all_candidate_skills)[:5]

    # Skill proofs
    skill_proofs = []
    for lang in list(candidate_langs)[:5]:
        lang_repos = [r for r in repos if r.get("language", "").lower() == lang]
        if lang_repos:
            total_lang_commits = sum(r["commits"] for r in lang_repos)
            skill_proofs.append({
                "skill": lang.capitalize(),
                "proof": f"{len(lang_repos)} repos, {total_lang_commits} commits",
                "confidence": min(0.99, 0.5 + total_lang_commits / 500)
            })

    return {
        "technical_score": round(tech_score, 1),
        "code_quality_score": round(quality_score, 1),
        "learning_velocity_score": round(velocity_score, 1),
        "collaboration_score": round(collab_score, 1),
        "skill_alignment_score": round(alignment_score, 1),
        "total_score": round(final_score, 1),
        "confidence": round(min(0.99, 0.5 + total_commits / 1000), 2),
        "skill_gaps": skill_gaps,
        "skill_proofs": skill_proofs,
    }
