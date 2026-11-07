# Setting up the public repository

For the maintainer, at the first publication. Run these from the repository root.
Install `gh` and run `gh auth login` first.

## What goes public

The full history, as it is. `research/captures/` is ignored by git and never goes.

## Create it

Topics and description come before the push: the first CI run's HACS validation
checks them.

```sh
gh repo create rp9376/orca-heatpump-ha --public --source . --remote origin \
  --description "Home Assistant integration for Orca Energija heat pumps"
gh repo edit rp9376/orca-heatpump-ha \
  --add-topic home-assistant --add-topic hacs --add-topic heat-pump --add-topic orca \
  --enable-wiki=false
git push -u origin main
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
