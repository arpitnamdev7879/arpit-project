from github import Github, GithubException
from config import GITHUB_TOKEN
from datetime import datetime, timezone
import math

gh = Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()


def audit_github(username: str) -> dict:
    """Perform deep audit of a GitHub user's profile and repositories."""
    try:
        user = gh.get_user(username)
    except GithubException as e:
        return {"error": f"GitHub user not found: {username}", "username": username}

    profile = {
        "username": username,
        "name": user.name or username,
        "bio": user.bio or "",
        "avatar_url": user.avatar_url,
        "location": user.location or "",
        "public_repos": user.public_repos,
        "followers": user.followers,
        "following": user.following,
        "created_at": user.created_at.isoformat() if user.created_at else "",
        "repos": [],
        "languages": {},
        "total_commits": 0,
        "total_stars": 0,
        "total_prs": 0,
    }

    repos = []
    try:
        all_repos = list(user.get_repos())
        # Sort by stars + activity, take top 8
        all_repos.sort(key=lambda r: (r.stargazers_count + r.forks_count), reverse=True)
        top_repos = [r for r in all_repos if not r.fork][:8]

        for repo in top_repos:
            try:
                commits = repo.get_commits(author=username)
                commit_count = 0
                recent_commits = []
                commit_dates = []

                for i, c in enumerate(commits):
                    if i >= 50:  # Limit for speed
                        break
                    commit_count += 1
                    commit_dates.append(c.commit.author.date)
                    if i < 5:
                        recent_commits.append({
                            "sha": c.sha[:7],
                            "message": c.commit.message.split('\n')[0][:80],
                            "date": c.commit.author.date.isoformat()
                        })

                # Detect language
                try:
                    langs = repo.get_languages()
                    for lang, bytes_count in langs.items():
                        profile["languages"][lang] = profile["languages"].get(lang, 0) + bytes_count
                except Exception:
                    pass

                # Commit consistency (days active)
                days_active = 0
                if commit_dates:
                    first = min(commit_dates)
                    last = max(commit_dates)
                    span = (last - first).days or 1
                    days_active = min(100, int((commit_count / max(span / 30, 1)) * 10))

                repo_data = {
                    "name": repo.name,
                    "description": repo.description or "",
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language or "Unknown",
                    "commits": commit_count,
                    "recent_commits": recent_commits,
                    "has_readme": False,
                    "has_tests": False,
                    "days_active": days_active,
                    "is_fork": repo.fork,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                }

                # Check for README
                try:
                    repo.get_readme()
                    repo_data["has_readme"] = True
                except Exception:
                    pass

                # Check for test files
                try:
                    contents = repo.get_contents("")
                    for f in contents:
                        name_lower = f.name.lower()
                        if any(t in name_lower for t in ["test", "spec", "pytest", "__test__"]):
                            repo_data["has_tests"] = True
                            break
                except Exception:
                    pass

                repos.append(repo_data)
                profile["total_commits"] += commit_count
                profile["total_stars"] += repo.stargazers_count

            except Exception as e:
                print(f"Error auditing repo {repo.name}: {e}")
                continue

    except Exception as e:
        print(f"Error fetching repos for {username}: {e}")

    profile["repos"] = repos

    # Count total languages by bytes
    total_bytes = sum(profile["languages"].values()) or 1
    profile["languages"] = {
        lang: round(bytes_count / total_bytes * 100, 1)
        for lang, bytes_count in sorted(profile["languages"].items(), key=lambda x: -x[1])
    }

    return profile
