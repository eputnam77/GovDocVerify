# Dependency Configuration Issues

The following dependency manifests contain unpinned versions which violate the repository policy against floating versions (`*`, `^`, `latest`).

- **package.json** and **package-lock.json**: dependencies use the `^` prefix.

Please pin each dependency to an exact version in `package.json` and regenerate `package-lock.json`.

Python dependencies are pinned and the Poetry lock file is in sync (checked via `pip-compile --dry-run`).

