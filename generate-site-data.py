#!/usr/bin/env python3
"""
generate-site-data.py

Scans all local repos, enriches project-config.json with live stats,
and writes projects.json + stats.json for the portfolio website.

Runs as a cron job via OpenClaw. The website reads these JSON files
and renders everything dynamically, so the site is always up to date
without touching the HTML.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_DIR = Path.home() / "projects"
SITE_DIR = PROJECTS_DIR / "studyalwaysbro.github.io"
CONFIG_FILE = SITE_DIR / "project-config.json"
PROJECTS_OUTPUT = SITE_DIR / "projects.json"
STATS_OUTPUT = SITE_DIR / "stats.json"

BINARY_EXTENSIONS = {
    ".pdf", ".parquet", ".pkl", ".pickle", ".npy", ".npz",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".7z",
    ".pyc", ".pyo", ".so", ".dll", ".exe",
    ".docx", ".xlsx", ".pptx",
    ".dump", ".db", ".sqlite", ".sqlite3",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".sql", ".css", ".html",
    ".mjs", ".cjs", ".vue", ".svelte", ".go", ".rs", ".rb",
}

EXCLUDE_DIRS = {
    ".venv", "venv", ".git", "__pycache__", "node_modules",
    "dist", ".next", "reports", ".tox", ".mypy_cache",
}


def run_git(cmd, cwd):
    try:
        result = subprocess.run(
            ["git"] + cmd, cwd=cwd,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def count_loc(repo_path):
    """Count lines of source code, excluding generated/vendor dirs."""
    total = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in SOURCE_EXTENSIONS:
                try:
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="replace") as fh:
                        total += sum(1 for _ in fh)
                except Exception:
                    pass
    return total


def get_repo_stats(repo_path):
    """Get live stats from a git repo."""
    stats = {
        "loc": 0,
        "commits": 0,
        "last_commit_date": None,
        "last_commit_msg": "",
        "contributors": 0,
        "is_git": False,
    }

    git_dir = Path(repo_path) / ".git"
    if not git_dir.exists():
        stats["loc"] = count_loc(repo_path)
        return stats

    stats["is_git"] = True
    stats["loc"] = count_loc(repo_path)

    # Commit count
    count = run_git(["rev-list", "--count", "HEAD"], repo_path)
    stats["commits"] = int(count) if count.isdigit() else 0

    # Last commit
    log = run_git(["log", "-1", "--format=%aI|||%s"], repo_path)
    if "|||" in log:
        date_str, msg = log.split("|||", 1)
        stats["last_commit_date"] = date_str
        stats["last_commit_msg"] = msg[:80]

    # Contributors
    authors = run_git(["log", "--format=%aE", "--all"], repo_path)
    if authors:
        stats["contributors"] = len(set(authors.splitlines()))

    return stats


def days_since(iso_date):
    """Convert ISO date to days ago."""
    if not iso_date:
        return None
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return delta.days
    except Exception:
        return None


def activity_label(days):
    """Human readable activity label."""
    if days is None:
        return "unknown"
    if days <= 1:
        return "today"
    if days <= 7:
        return "this week"
    if days <= 30:
        return "this month"
    if days <= 90:
        return "recently"
    return "a while ago"


CATEGORY_COLORS = {
    "Bot": "#f59e0b",
    "Research": "#e94560",
    "ML Pipeline": "#4361ee",
    "Automation": "#4361ee",
    "Learning Project": "#2dd4bf",
    "Utility": "#2dd4bf",
    "Unknown": "#8888aa",
}


def detect_category(repo_path):
    """Guess project category from files present."""
    p = Path(repo_path)
    files = {f.name for f in p.iterdir() if f.is_file()}
    dirs = {d.name for d in p.iterdir() if d.is_dir()}

    if "bot.js" in files or "discord" in str(p).lower():
        return "Bot"
    if "train" in " ".join(files).lower() or "model" in " ".join(dirs).lower():
        return "ML Pipeline"
    if any(f.endswith(".ipynb") for f in files):
        return "Research"
    if "package.json" in files and ("src" in dirs or "components" in dirs):
        return "Learning Project"
    return "Unknown"


def detect_tags(repo_path):
    """Guess tech stack from files."""
    p = Path(repo_path)
    tags = set()
    all_files = []
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        all_files.extend(files)
        if len(all_files) > 500:
            break

    ext_counts = {}
    for f in all_files:
        ext = Path(f).suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    if ext_counts.get(".py", 0) > 3:
        tags.add("Python")
    if ext_counts.get(".js", 0) > 3 or ext_counts.get(".mjs", 0) > 0:
        tags.add("Node.js")
    if ext_counts.get(".ts", 0) > 3 or ext_counts.get(".tsx", 0) > 0:
        tags.add("TypeScript")
    if ext_counts.get(".jsx", 0) > 0 or ext_counts.get(".tsx", 0) > 0:
        tags.add("React")
    if (p / "requirements.txt").exists() or (p / "pyproject.toml").exists():
        tags.add("Python")
    if (p / "package.json").exists():
        try:
            pkg = json.loads((p / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "discord.js" in deps:
                tags.add("discord.js")
            if "react" in deps:
                tags.add("React")
            if "tensorflow" in " ".join(all_files).lower():
                tags.add("TensorFlow")
        except Exception:
            pass

    return sorted(tags) if tags else ["Code"]


def humanize_name(dir_name):
    """Turn a directory name into something presentable."""
    name = dir_name.replace("-", " ").replace("_", " ")
    return " ".join(w.capitalize() for w in name.split())


def auto_discover_repos(config):
    """Find repos not in config and add them with safe defaults."""
    known_paths = {p["repo_path"] for p in config["projects"]}
    excluded = set(config.get("excluded_repos", []))
    new_projects = []

    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        if d.name in excluded:
            continue

        # Check all known repo_path values (handles nested like Polymarket-Agents/...)
        is_known = False
        for kp in known_paths:
            if d.name == kp or d.name == kp.split("/")[0]:
                is_known = True
                break
        if is_known:
            continue

        # Skip if no source code at all
        stats = get_repo_stats(str(d))
        if stats["loc"] < 50:
            continue

        category = detect_category(str(d))
        tags = detect_tags(str(d))
        color = CATEGORY_COLORS.get(category, "#8888aa")

        proj = {
            "id": d.name.lower().replace(" ", "-"),
            "name": humanize_name(d.name),
            "repo_path": d.name,
            "github": None,
            "category": category,
            "color": color,
            "featured": False,
            "visible": False,  # hidden by default until reviewed
            "description": f"Auto-discovered project. Edit project-config.json to add a description and set visible to true.",
            "tags": tags,
            "_auto_discovered": True,
        }
        new_projects.append(proj)
        print(f"  NEW: {d.name} ({category}, {stats['loc']} LOC)")

    return new_projects


def generate_projects():
    """Load config, auto-discover new repos, enrich with live stats, write projects.json."""
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    # Auto-discover new repos and add to config
    new_repos = auto_discover_repos(config)
    if new_repos:
        print(f"\n  Auto-discovered {len(new_repos)} new repo(s), adding to config (hidden by default)")
        config["projects"].extend(new_repos)
        # Write updated config back so new repos persist
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    enriched = []
    for proj in config["projects"]:
        repo_path = PROJECTS_DIR / proj["repo_path"]
        if not repo_path.exists():
            print(f"  SKIP {proj['name']}: path not found ({repo_path})")
            continue

        stats = get_repo_stats(str(repo_path))
        days = days_since(stats["last_commit_date"])

        entry = {
            "id": proj["id"],
            "name": proj["name"],
            "category": proj["category"],
            "color": proj["color"],
            "featured": proj["featured"],
            "visible": proj["visible"],
            "description": proj["description"],
            "tags": proj["tags"],
            "github": proj.get("github"),
            "stats": {
                "loc": stats["loc"],
                "commits": stats["commits"],
                "last_activity": activity_label(days),
                "last_commit_date": stats["last_commit_date"],
                "last_commit_msg": stats["last_commit_msg"],
            },
        }
        enriched.append(entry)

        loc_display = f"{stats['loc'] // 1000}K+" if stats['loc'] >= 1000 else str(stats['loc'])
        print(f"  {proj['name']}: {loc_display} LOC, {stats['commits']} commits, {activity_label(days)}")

    # Sort: featured first, then by commit count
    enriched.sort(key=lambda x: (not x["featured"], -x["stats"]["commits"]))

    with open(PROJECTS_OUTPUT, "w") as f:
        json.dump({"projects": enriched, "generated": datetime.now(timezone.utc).isoformat()}, f, indent=2)

    print(f"\nWrote {len(enriched)} projects to {PROJECTS_OUTPUT}")
    return enriched


def generate_stats(projects):
    """Aggregate stats across all repos and write stats.json."""
    total_loc = 0
    total_commits = 0
    total_python = 0

    # Count across ALL repos (not just configured projects)
    for d in PROJECTS_DIR.iterdir():
        if not d.is_dir():
            continue
        if d.name in ("studyalwaysbro.github.io", "actual-budget", "actual-dashboard"):
            continue

        # LOC
        loc = count_loc(str(d))
        total_loc += loc

        # Commits
        if (d / ".git").exists():
            count = run_git(["rev-list", "--count", "HEAD"], str(d))
            total_commits += int(count) if count.isdigit() else 0

    # Python script count
    for root, dirs, files in os.walk(PROJECTS_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".py"):
                total_python += 1

    # Count project dirs
    project_count = sum(1 for d in PROJECTS_DIR.iterdir() if d.is_dir() and d.name != "studyalwaysbro.github.io")

    loc_display = f"{total_loc // 1000}K+" if total_loc >= 1000 else str(total_loc)

    stats = {
        "loc": total_loc,
        "loc_display": loc_display,
        "python_scripts": total_python,
        "projects": project_count,
        "commits": total_commits,
        "data_sources": 8,
        "active_projects": sum(1 for p in projects if p["visible"] and p["stats"]["commits"] > 0),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open(STATS_OUTPUT, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\nStats: {loc_display} LOC, {total_python} Python scripts, {total_commits} commits, {project_count} projects")
    return stats


def main():
    print(f"generate-site-data.py @ {datetime.now().strftime('%Y-%m-%d %H:%M ET')}\n")
    projects = generate_projects()
    generate_stats(projects)
    print("\nDone.")


if __name__ == "__main__":
    main()
