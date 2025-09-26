# AGENTS.md

*Authoritative playbook for this repository’s **OpenAI Codex** multi‑agent workflow*

---

## 0 · Global Settings

| Key                       | Value                                                                     |
| ------------------------- | ------------------------------------------------------------------------- |
| Default shell             | `bash` (Linux)                                                            |
| Supported Python versions | **3.12 (primary)** · 3.11 (CI only)                                       |
| Virtual‑env manager       | **uv** (falls back to `python -m venv`)                                   |
| Dependency manager        | **Poetry** (`poetry install && poetry lock`) → synced via **uv pip sync** |
| Package lock‑source       | **`poetry.lock`** (single source of truth)                                |
| Code formatter            | **Black**                                                                 |
| Import / lint / fix       | **Ruff** (`ruff check`, `ruff format`)                                    |
| Static‑type checker       | **MyPy --strict**                                                         |
| Test runner               | **Pytest**                                                                |
| Property‑based tests      | **Hypothesis**                                                            |
| E2E framework             | _Disabled in sandbox_                                                     |
| Mutation testing          | _Disabled in sandbox_                                                     |
| Coverage thresholds       | 70 % (feature) → 90 % (main) (**branch + line**)                          |
| Mutation score            | _No requirement in sandbox_                                               |
| SAST scanners             | **Bandit**, **Semgrep**                                                   |
| Package/CVE scanners      | **pip‑audit**                                                             |
| Container scanners        | _Disabled in sandbox_                                                     |
| Docs generator            | **MkDocs‑Material** (`mkdocs build`)                                      |
| Commit style              | **Conventional Commits**                                                  |
| CI provider               | **GitHub Actions** *(experimental – see §5)*                              |

> **Data flow**  Each agent works off the latest commit on its branch, communicates **only** via Issues / PRs, and acquires an `agent‑running` lock‑label to avoid concurrent pushes.

---

## 1 · Agents & Execution Order

| #  | Agent ID       | Purpose (one‑liner)                                                                             | Auto‑trigger condition               |
| -- | -------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------ |
| 0  | `planner`      | Parse **PRD.md** → create **TASKS.md** (epics → issues with A/C & labels).                      | manual                               |
| 1  | `architect`    | Design folder layout, write ADRs, bootstrap Poetry + CI skeleton.                               | `planner` PR merged                  |
| 2  | `scaffolder`   | Generate skeleton code **and tests** for every open issue.                                      | `architect` PR merged                |
| 3  | `scenario‑gen` | Convert acceptance criteria to Gherkin *.feature* files & Hypothesis strategies.                | new `ready` issue                    |
| 4  | `verifier`     | Cross‑check **PRD.md** ↔ **TASKS.md** ↔ code; emit completeness report.                         | after `scenario‑gen`                 |
| 5  | `optimizer`    | Profile hot paths (Py‑perf, cProfile, Lighthouse); propose caching / SQL / async optimisations. | after `verifier:success`             |
| 6  | `builder`      | Implement code for `ready` issues; maintain coverage ≥75 % (dev gate).                          | after `optimizer:success`            |
| 7  | `linter`       | Run Ruff + Black; open PR if diff.                                                              | after `builder:success`              |
| 8  | `tester`       | Run **dev gate** (unit + property tests, MyPy, coverage ≥70 %).                                 | after `linter:success`               |
| 9  | `fixer`        | On any gate failure: add/adjust tests **then** patch code; iterate until green.                 | on failure (lint/test)               |
| 10 | `security`     | Bandit + Semgrep + pip‑audit; open high‑severity CVE issues.                                    | nightly · before merge→`main`        |
| 11 | `docwriter`    | Update README, API refs, examples, changelog; ensure MkDocs passes.                             | branch green & cov ≥90 %             |
| 12 | `reviewer`     | Human‑style review; request approvals.                                                          | after `docwriter:success`            |
| 13 | `releasebot`   | Bump semver, tag, and draft GitHub release notes (container scanning handled externally).       | PR merged→`main`                     |

### Agent‑handoff rules

* Success → add `ready‑for:<next‑agent>` **and** remove `agent‑running`.
* **Feature branches** enforce the *dev gate* (coverage ≥70 %).
* **main** enforces the *release gate* (coverage ≥90 %, security & docs pass).

---

## 2 · Quality Gates

### Dev Gate (feature branches)

```bash
ruff check src tests
black --check src tests
mypy --strict src tests
bandit -r src -lll --skip B101               # allow asserts early
semgrep --config p/ci                       # lightweight SAST
pytest -q --cov=govdocverify --cov-branch --cov-fail-under=70
```

### Release Gate (main)

```bash
ruff check src tests
black --check src tests
mypy --strict src tests
bandit -r src -lll
semgrep --config p/default
pip-audit -r requirements.txt
pytest -q --cov=govdocverify --cov-branch --cov-fail-under=90
mkdocs build --strict
```

Any non‑zero exit hands control to **fixer**.

---

## 3 · Documentation Standards

### Tone & Voice

* **Friendly, conversational, inclusive** – write as if explaining to a colleague over coffee.
* **Active voice** – “The system processes data,” not “Data is processed by the system.”
* **Confident and helpful** – encourage and build user confidence.
* **Avoid jargon** – prefer clear, plain language.
* **Celebrate user success** – frame features as enabling goals.

### Structure & Formatting

* Clear, hierarchical headings (H1 → H2 → H3).
* A runnable **code example for every feature**.
* Numbered, step‑by‑step instructions for complex flows.
* Cross‑references to related docs and external resources.

### Content Guidelines

* **Start with the problem** a feature solves before diving into how.
* Provide **real‑world use‑cases**.
* Document common errors and their remedies.
* Note any **performance implications or limitations**.

### Technical Writing Standards

* **Consistent terminology** across all docs.
* API docs include **parameter types, return values, examples**.
* Changelog follows **Keep a Changelog**.
* README layout: Install → Quick‑start → Features → Contributing → License.

### Templates

* `templates/README.md` – canonical README structure.
* `templates/API_DOCS.md` – API reference template.
* `templates/CHANGELOG.md` – release‑notes skeleton.

---

## 4 · Branch & Commit Policy

* **Branch prefixes**: `plan/<slug>` · `scaffold/<slug>` · `feat/<slug>` · `fix/<issue>` · `docs/<topic>` · `test/<scope>`
* **Commits** follow Conventional Commits. Examples:

  ```text
  feat/auth: add OAuth2 login flow
  fix/api: prevent division‑by‑zero in calculator
  chore/ci: raise coverage threshold to 90%
  ```
* Default merge strategy: **squash‑merge** with required‑status checks on `main`.

---

## 5 · Environment Setup

```bash
# create & activate virtual‑env
uv venv "3.12"              # or "3.11" for compatibility work

# install locked dependencies
poetry install               # generates poetry.lock if missing
poetry sync                  # remove extras not in the lock file
uv pip sync pyproject.toml   # reproduce lock inside venv

# enable pre‑commit hooks (Ruff / Black / MyPy / etc.)
pre-commit install
```

Codespaces / VS Code: the `devcontainer.json` automatically runs `pre‑commit` on file‑save.

---

## 6 · Failure‑Recovery Matrix

| Problem                                 | Responsible Agent | Remedy                                          |
| --------------------------------------- | ----------------- | ----------------------------------------------- |
| Lint error                              | linter            | Auto‑fix & push                                 |
| Type error                              | tester → fixer    | Patch types/code                                |
| Unit / integration / property test fail | fixer             | Add/adjust tests **then** patch code            |
| E2E failure                             | fixer             | _Skipped in sandbox_                              |
| Mutation score drop                     | fixer             | _Not applicable in sandbox_                     |
| Coverage drop                           | builder / tester  | Add tests or mark legitimate exclusions         |
| Performance regression (≥15 % slower)   | optimizer         | Profile again, implement caching/indexing/async |
| High CVE (pip‑audit)                     | security          | Bump dependency or patch                          |
| SAST finding (Semgrep)                  | security → fixer  | Investigate & patch                             |
| Docs build failure                      | docwriter         | Regenerate or repair docs                       |

---

## 7 · Project Structure & File Organisation

### Recommended Repository Layout

```
your-project/
├── src/                     # Distribution code
│   └── your_package/
├── tests/                   # Unit / property / integration tests
├── docs/                    # User‑facing docs (built by MkDocs)
├── scripts/                 # Dev / CI helper scripts
├── .github/
├── .dev/                    # ⚠️  NOT packaged
│   ├── AGENTS.md            # this playbook
│   ├── TASKS.md             # task backlog
│   ├── PRD.md               # product requirements
│   ├── ADRs/
│   └── templates/
├── pyproject.toml
├── requirements-dev.txt
├── .pre-commit-config.yaml
└── README.md
```

Add this to `pyproject.toml` to exclude dev files from wheels:

```toml
[tool.setuptools.packages.find]
where = ["src"]
exclude = ["tests*", ".dev*"]
```

---

*End of AGENTS.md*
