# Setting up the public repository

For the maintainer, at the first publication. Run these from the repository root.
Install `gh` and run `gh auth login` first.

## What goes public

Everything except three private working files:

| File | Why it stays out |
|---|---|
| `PLAN.md` | The pump's local address and details of one house |
| `CLAUDE.md` | Rules for the agents working from that plan |
| `docs/progress.md` | The working log, with the maintainer's own notes and decisions |

`research/` has to stay: the tests load `moja_orca_catalog.json` and
`tag_registers.json` from it. `research/captures/` is ignored by git and never goes.

The local history holds the address too, so removing files isn't enough. The first
push is a single fresh commit, on a new branch. The old branch stays local as the
private history, and the three files stay on disk.

## Make the public branch

The commit's author address becomes public. To use GitHub's private one instead, run
`git config user.email "<id>+rp9376@users.noreply.github.com"` first (the address is
on github.com/settings/emails).

```sh
git checkout --orphan public
git rm --cached -q PLAN.md CLAUDE.md docs/progress.md
printf 'PLAN.md\nCLAUDE.md\ndocs/progress.md\n' >> .git/info/exclude
git commit -m "Orca Heat Pump 1.0.0b1"
```

## Create it

Topics and description come before the push: the first CI run's HACS validation
checks them.

```sh
gh repo create rp9376/orca-heatpump-ha --public --source . --remote origin \
  --description "Home Assistant integration for Orca Energija heat pumps"
gh repo edit rp9376/orca-heatpump-ha \
  --add-topic home-assistant --add-topic hacs --add-topic heat-pump --add-topic orca \
  --enable-wiki=false
git push -u origin public:main
```

Work continues on the local `public` branch.

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
