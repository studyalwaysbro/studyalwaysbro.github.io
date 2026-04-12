# Public Truth Audit

**Date:** 2026-04-12
**Scope:** Compare website claims vs public GitHub reality + identify security/compliance gaps

## Public GitHub Profile (studyalwaysbro)

6 public repos, 88 total public commits across all repos.

| Repo | Language | Commits | Last Push | Fork? | On Site? |
|------|----------|---------|-----------|-------|----------|
| asset-cluster-migration | Python | 1 | 2026-04-02 | No | Yes (visible) |
| Ice-Cream-Production-Forecasting | Jupyter | 6 | 2025-11-21 | No | **No** |
| intro-ml-study | HTML | 5 | 2026-03-15 | No | **No** |
| jenkins-discord-bot | JavaScript | 4 | 2026-04-02 | No | Yes (visible) |
| Polymarket_Agents | Python | 19 | 2026-04-12 | Yes (mwhite732) | Yes (visible) |
| studyalwaysbro.github.io | HTML | 53 | 2026-04-11 | No | N/A (is the site) |

## Mismatches Found

### 1. stats.json "commits": 58 vs reality: stale + wrong scope

The stat counted commits from ALL local repos (including private). Public GitHub alone has 88 commits. The number is both stale and mixing private/public sources without disclosure.

**Fix:** Only aggregate from visible projects. Use GitHub API for public repos, local git for private visible ones.

### 2. stats.json "loc": 132,546 includes hidden and non-configured repos

The LOC scan walks ALL directories in ~/projects/, including hidden projects, excluded repos, and projects not on the site. This inflates the number and potentially leaks scope.

**Fix:** Only aggregate from visible projects in project-config.json.

### 3. stats.json "projects": 14 counts all directories

14 is the count of directories in ~/projects/ minus excluded. The site only shows 7 visible projects. This number implies a scope the visitor can't verify.

**Fix:** Show count of visible projects only (currently 7).

### 4. stats.json "data_sources": 8 is hardcoded and misleading

This refers specifically to Polymarket's 8 data sources. Displayed as a portfolio-level stat on the hero section, it implies 8 data sources across the whole portfolio, which isn't accurate.

**Fix:** Replace with "Public Repos" (6) sourced from GitHub API, or remove.

### 5. stats.json "python_scripts": 391 scans all local repos

Same issue as LOC. Scans everything, not just visible projects.

**Fix:** Only count from visible project directories.

### 6. projects.json publishes commit messages from private repos

`last_commit_msg` is included for all projects including private ones. Commit messages from private repos could contain sensitive context.

**Fix:** Only include `last_commit_msg` for public repos. Omit or blank for private repos.

### 7. Commit count mismatches

| Project | projects.json says | GitHub public says |
|---------|--------------------|--------------------|
| Asset Cluster Migration | 23 commits | 1 commit |
| Jenkins the Law | 21 commits | 4 commits |
| Polymarket Agents | 14 commits | 19 commits |

Local git history doesn't match public GitHub. Likely because squashed pushes or force-pushes reduced public commit count. The local number is the true development effort, but the public number is the verifiable one.

**Fix:** For public repos, use GitHub API commit count (verifiable). For private repos, use local git count (not verifiable but honest about development effort). Document this distinction.

### 8. Polymarket Agents repo_path is stale

Config points to `Polymarket-Agents/Polymarket_Agents-main` (old nested directory). New clean clone is at `Polymarket_Agents`.

**Fix:** Update repo_path.

### 9. Missing public repos from site

Two public repos are on GitHub but not on the portfolio:
- **Ice-Cream-Production-Forecasting** (ARIMA/SARIMA project, Jupyter)
- **intro-ml-study** (ML study guide, HTML)

These are legitimate public projects but may not be portfolio-worthy. Needs manual review.

### 10. Jenkins "Telegram" tag bypasses blocked tags

The compliance rules block the "Telegram" tag except for projects on the `platform_tag_allowlist`. Jenkins IS on the allowlist (`jenkins-discord-bot`), but publicly advertising Telegram deployment could be a concern.

**Review:** Is having "Telegram" in Jenkins' tags intentional? The tag is currently visible on the site.

## Security Assessment

### Currently Safe
- No employer names on site (besides Stevens)
- Private repos show "Private Repository" label, not links
- Hidden projects stay hidden
- Disclaimers are solid
- No API keys, tokens, or credentials exposed
- No hostnames, IPs, or infrastructure details

### Issues Fixed by This Upgrade
- Private commit messages no longer published
- Stats no longer inflated by hidden/non-configured repos
- Verifiable numbers sourced from public APIs where possible
- Compliance config is explicit and auditable

### Items Needing Manual Review
1. Whether to add Ice-Cream-Production-Forecasting and intro-ml-study to the site
2. Whether the "Telegram" tag on Jenkins is acceptable
3. Whether private project LOC/commit counts should be shown at all (currently shown)
4. Review of all project descriptions for compliance (already passing, but worth a human read)

## Recommendations Implemented

1. Refactored `generate-site-data.py` to only aggregate from visible projects
2. Added `compliance_config.json` with explicit allowlists
3. Strip commit messages from private repos in public output
4. Replace "Data Sources" hero stat with "Public Repos" from GitHub API
5. Fix Polymarket repo_path
6. Upgraded `truthsync.yaml` to validate generated outputs
7. Created this audit and architecture documentation
