# 0015. The Marketplace installs from the repository, not a release zip

Status: Accepted (user, 2026-11-08)

## Context
`hacs.json` had `zip_release` with `orca_heatpump.zip`. With that, Home Assistant
2026.11's Marketplace always downloads the zip from a release named after the version
it installs. Our only release is a pre-release, which it skips unless beta versions are
switched on, so it picked the `main` branch and asked for
`releases/download/main/orca_heatpump.zip`: a 404, and the install failed. Seen on the
user's Home Assistant and reproduced on the dev container.

The Marketplace also refuses zip releases for repositories in its catalog
(`catalog_zip_release`), so the setting would block the default store later.

## Decision
No `zip_release`. The Marketplace installs `custom_components/orca_heatpump` from the
repository at the version it picks: a release tag, or the default branch while there is
no stable release. The release workflow still checks the tag against `manifest.json`
and attaches the zip for manual installs.

## Consequences
- Installs work with only a pre-release, and after a stable release.
- While there is no stable release, a default install follows `main`, not the newest
  pre-release. Switching on beta versions for the repository installs the pre-release.
