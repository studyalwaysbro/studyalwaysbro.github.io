# Website Truth System Architecture

## Trust Model

```
project-config.json          (manual, raw, source of truth)
        |
        v
compliance_config.json       (allowlists, safety rules)
        |
        v
generate-site-data.py        (collects, filters, validates)
        |
        +---> projects.json  (safe public output)
        +---> stats.json     (safe public output)
        +---> truth-sync-report.json  (validation report)
        |
        v
index.html                   (renders safe data only)
```

## Trust Boundaries

### What's Safe to Publish

- Public repo names and URLs (from GitHub API)
- Approved project descriptions (manually reviewed in project-config.json)
- Tags/categories (after compliance filter)
- Aggregate stats from visible projects only
- Public repo commit counts from GitHub API
- Language info from GitHub API
- Last-updated dates for public repos

### What Gets Blocked

- Private repo names not intentionally shown on the site
- Local filesystem paths
- Commit messages from private repos
- Internal operational details (cron schedules, service configs)
- Infrastructure info (hostnames, IPs, machine specs)
- Anything matching compliance blocked phrases
- Stats from hidden or excluded repos

### Ambiguous (requires explicit approval)

- LOC counts for private repos (currently shown because projects are visible by choice)
- Local git commit counts for private repos (not verifiable by visitors)
- Project descriptions for private repos (must pass compliance review)

## Data Sources

### Canonical Sources

1. **project-config.json** - manually curated project list with descriptions, categories, visibility
2. **GitHub API** - public repo metadata, commit counts, languages, push dates
3. **Local git repos** - LOC counts, local commit history (for private repos only)

### Derived Outputs

1. **projects.json** - enriched project data for the site (compliance-filtered)
2. **stats.json** - aggregate metrics for the hero section
3. **truth-sync-report.json** - validation results

## Compliance Config

`compliance_config.json` controls:

- **`visible_projects_only`**: if true, stats only aggregate from visible projects
- **`github_username`**: for API queries
- **`public_repos_for_commits`**: use GitHub API for public repo commit counts
- **`strip_private_commit_msgs`**: remove commit messages from private repos
- **`blocked_phrases`**: phrases that trigger compliance violation (base64 in script for hook compat)
- **`blocked_tags`**: tags blocked from public display
- **`platform_tag_allowlist`**: projects exempt from tag blocking
- **`stat_labels`**: mapping of stat keys to display labels (controls hero section)

## Generation Flow

1. **Load** project-config.json
2. **Auto-discover** new repos (added as hidden by default)
3. **Fetch** GitHub API data for public repos
4. **Enrich** each visible project with local git stats
5. **Apply compliance filter** on descriptions and tags
6. **Sanitize** output: strip commit messages from private repos
7. **Aggregate stats** from visible projects only
8. **Validate** outputs against truth sources
9. **Write** projects.json, stats.json, truth-sync-report.json
10. **Block** if any compliance violations found

## Regenerating Site Data

```bash
cd ~/projects/studyalwaysbro.github.io
python3 generate-site-data.py
```

This regenerates projects.json, stats.json, and truth-sync-report.json.

Review the truth-sync report before committing:
```bash
cat truth-sync-report.json | python3 -m json.tool
```

## Truth Sync

The `truthsync.yaml` validates:
- stats.json exists and was generated recently
- projects.json exists and was generated recently
- All visible projects in project-config.json appear in projects.json
- No compliance violations in current data
- Generated timestamps are not stale (configurable threshold)

## Manual Review Checklist

Before pushing site changes:

1. Run `python3 generate-site-data.py` and check for compliance violations
2. Review truth-sync-report.json for warnings
3. Spot-check projects.json for any private data leakage
4. Verify stats.json numbers are reasonable
5. Open index.html locally to verify the site looks right
6. Check git diff for anything unexpected
