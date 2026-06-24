import math
from datetime import datetime, timezone


def compute_fraud_score(github_data: dict) -> dict:
    """Detect fake or exaggerated GitHub profiles."""
    signals = []
    repos = github_data.get("repos", [])
    total_stars = github_data.get("total_stars", 0)
    total_commits = github_data.get("total_commits", 0)
    public_repos = github_data.get("public_repos", 0)
    followers = github_data.get("followers", 0)
    following = github_data.get("following", 1)

    # Signal 1: Star farming — high stars, very low commits
    for repo in repos:
        if repo["stars"] > 100 and repo["commits"] < 5:
            signals.append({
                "type": "star_farming",
                "weight": 0.4,
                "detail": f"Repo '{repo['name']}' has {repo['stars']} stars but only {repo['commits']} commits"
            })

    # Signal 2: Fork abuse — many repos are forks
    fork_count = sum(1 for r in repos if r.get("is_fork", False))
    if len(repos) > 0:
        fork_ratio = fork_count / len(repos)
        if fork_ratio > 0.7:
            signals.append({
                "type": "fork_abuse",
                "weight": 0.3,
                "detail": f"{int(fork_ratio * 100)}% of repos are forks with no original work"
            })

    # Signal 3: Empty repos — repos with 0-1 commits
    empty_repos = sum(1 for r in repos if r["commits"] <= 1)
    if empty_repos > 3:
        signals.append({
            "type": "empty_repos",
            "weight": 0.2,
            "detail": f"{empty_repos} repos have 0-1 commits (placeholder repos)"
        })

    # Signal 4: No README on most repos
    no_readme = sum(1 for r in repos if not r.get("has_readme", False))
    if len(repos) > 0 and no_readme / len(repos) > 0.8:
        signals.append({
            "type": "poor_documentation",
            "weight": 0.15,
            "detail": f"{no_readme} out of {len(repos)} repos have no README"
        })

    # Signal 5: Suspicious follower ratio
    if following > 0 and followers / following > 50 and total_commits < 100:
        signals.append({
            "type": "follower_manipulation",
            "weight": 0.25,
            "detail": f"High follower/following ratio ({followers}/{following}) with low activity"
        })

    # Signal 6: Very new account with inflated repos
    try:
        created = datetime.fromisoformat(github_data.get("created_at", "2020-01-01").replace("Z", "+00:00"))
        account_age_days = (datetime.now(timezone.utc) - created).days
        if account_age_days < 180 and public_repos > 50:
            signals.append({
                "type": "suspicious_account_age",
                "weight": 0.35,
                "detail": f"Account only {account_age_days} days old with {public_repos} repos"
            })
    except Exception:
        pass

    # Compute fraud score
    if not signals:
        fraud_score = 0.0
    else:
        weighted_sum = sum(s["weight"] for s in signals)
        max_weight = max(s["weight"] for s in signals)
        fraud_score = min(1.0, (weighted_sum / len(signals)) + max_weight * 0.3)
        fraud_score = round(fraud_score, 3)

    # Risk level
    if fraud_score < 0.2:
        risk_level = "Low"
    elif fraud_score < 0.4:
        risk_level = "Medium"
    elif fraud_score < 0.6:
        risk_level = "High"
    else:
        risk_level = "Critical"

    return {
        "fraud_score": fraud_score,
        "risk_level": risk_level,
        "signals": signals,
        "flagged": fraud_score >= 0.5
    }
