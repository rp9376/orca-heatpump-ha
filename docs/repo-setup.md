# Setting up the public repository

For the maintainer, at the first publication. Run these from the repository root
after installing `gh` and running `gh auth login`.

## Before the first push

`PLAN.md` and `research/protocol.md` hold the pump's local address and login. Decide
what to do with them: remove them from the files, or keep `PLAN.md`, `research/` and
`CLAUDE.md` out of the public repository. Local history contains them too, so removing
them from the files alone isn't enough; pushing a fresh history is the simple way.

## Create it

```sh
gh repo create rp9376/orca-heatpump-ha --public --source . --push \
  --description "Home Assistant integration for Orca Energija heat pumps"
gh repo edit rp9376/orca-heatpump-ha \
  --add-topic home-assistant --add-topic hacs --add-topic heat-pump --add-topic orca \
  --enable-wiki=false
```

## Protect the main branch

Once CI has run once, so the checks exist:

```sh
gh api -X PUT repos/rp9376/orca-heatpump-ha/branches/main/protection --input - <<'JSON'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["Lint", "hassfest", "HACS validation", "Test (Home Assistant stable)"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

## Release

```sh
gh release create v1.0.0b1 --prerelease --title 1.0.0b1 --notes-file CHANGELOG.md
```

The release workflow checks the tag against `manifest.json` and attaches
`orca_heatpump.zip`, which HACS installs (`hacs.json`).
