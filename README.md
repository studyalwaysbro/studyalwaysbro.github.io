# Nicholas Tavares

Personal portfolio site. Background, projects, and experience in quantitative research and ML engineering.

**Live:** [studyalwaysbro.github.io](https://studyalwaysbro.github.io)

## Site Data Generation

The site loads `stats.json` and `projects.json` at runtime. These are generated from `project-config.json` through a compliance-first pipeline.

```bash
python3 generate-site-data.py
```

This:
1. Reads project-config.json (source of truth)
2. Enriches with live git stats and GitHub API data
3. Applies compliance filtering (blocked phrases, tag allowlists)
4. Strips private repo commit messages
5. Aggregates stats from visible projects only
6. Writes projects.json, stats.json, and truth-sync-report.json

See `docs/website_truth_system.md` for the full architecture.

## Files

| File | Role |
|------|------|
| `project-config.json` | Manual project registry (source of truth) |
| `compliance_config.json` | Allowlists and safety rules |
| `generate-site-data.py` | Compliance-first data generator |
| `projects.json` | Generated, safe public output |
| `stats.json` | Generated, visible projects only |
| `truth-sync-report.json` | Validation report |
| `index.html` | The site itself |
| `truthsync.yaml` | Truth sync validation config |
| `docs/` | Audit report and architecture docs |
