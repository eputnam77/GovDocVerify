# GovDocVerify

FAA‑style validation for Word docs—CLI, FastAPI, and React UI in one toolkit.

**GovDocVerify** scans Advisory Circulars, Orders, and other FAA artifacts for headings, formatting, terminology, and accessibility issues. It delivers:

* a **FastAPI** backend (live Swagger UI)
* a modern **React/Next.js** frontend with real‑time preview
* an easy **CLI** for local batch checks
* Displays document metadata (Title, Author, Last Modified By, Created, Modified)

Full technical docs live under **`docs/`**; start with *docs/getting‑started.md* when you’re ready to dig deeper.

## 📄 Supported document formats

GovDocVerify accepts only modern `.docx` files. Legacy formats—such as `.doc`, `.pdf`, `.rtf`, and `.txt`—are rejected during validation.

---

## ✨ Quick install (recommended)

For a one-shot setup run the helper script:

```bash
./scripts/setup_env.sh
```

It creates a local `.venv`, installs locked dependencies, and enables pre-commit hooks.

Prefer to do the steps manually? We follow the same pattern as the other CLI projects: **pipx** for global tool shims and **uv** for ultra‑fast Python/venv work with standard `setuptools` packaging.

```bash
# 0. One-time setup: Python & pipx -------------------------------------------------
python --version                # confirm Python 3.11–3.13
python -m pip install --user pipx
python -m pipx ensurepath       # restart shell if PATH changes
pipx install uv                 # fast resolver, venv mgr, lockfile, tool runner

# 1  Per project ────────────────────────────────────────────────────────
git clone https://github.com/eputnam77/GovDocVerify.git
cd GovDocVerify

# 2. Create and activate venv (Python 3.12) --------------------------------------
uv python install 3.12          # Download if not present
uv venv --python 3.12
# Activate the venv:
#   On Windows:
.venv\Scripts\activate
#   On Mac/Linux:
# source .venv/bin/activate

# 3. Install project + extras (dev, test, security) ------------------------------
uv pip install -e ".[dev,test,security]"
# (Optional) Allow prerelease dependencies if needed:
# uv pip install -e ".[dev,test,security]" --prerelease=allow

# 4. (Optional) Upgrade pip and pre-commit inside the venv -----------------------
uv pip install --upgrade pip pre-commit

# 5. Install Git hooks -----------------------------------------------------------
pre-commit install
```

---

## 🐍 Virtual‑env fallback (no uv)

```bash
python -m venv .venv
source .venv/bin/activate           # Win: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev,test,security]"
```

---

## 🔑 Environment variables (optional)

| Variable                  | Purpose                                 |
| ------------------------- | --------------------------------------- |
| `GOVDOCVERIFY_SECRET_KEY` | JWT signing key for the API             |
| `NEXT_PUBLIC_API_BASE`    | Override API URL for the React frontend |

Create a `.env` or export vars before running the backend.

---

## 🚀 Run the backend API

```bash
uvicorn govdocverify.api:app --reload --port 8000
# Automatic interactive docs at http://localhost:8000/docs
```

---

## 🖥️ Run the React frontend (Node 18+)

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env              # adjust NEXT_PUBLIC_API_BASE if backend separate
npm run dev
```

Open [http://localhost:3000/](http://localhost:3000/) and start uploading `.docx` files.

---

## 🛠️ CLI usage

```bash
govdocverify check mydoc.docx --type "Advisory Circular"
```

or the bare Python entry point:

```bash
python -m govdocverify.cli check mydoc.docx --type "Order"
```

---

## 🧪 Quality Checks & Testing Guide

This project uses a multi-tool testing pipeline to ensure code quality, formatting, type safety, security, and robustness. Below is the full suite of commands and best practices for local development and CI validation.

---

### 1. ✅ Lint, Format, and Static Type Checks

**Defined in `.pre-commit-config.yaml`** and run automatically before every commit (after running `pre-commit install`):

* **Ruff:** Linting and formatting for Python code (also handles import sorting)
* **Black:** Auto-formats Python code to a consistent style
* **Mypy:** Static type checking
* **Bandit:** Python code security scanning (see below for details)
* **mdformat:** Markdown linting and formatting, with Ruff rules
* **Codespell:** Checks for common spelling mistakes in code, comments, and docs

**To run all checks across the codebase:**

```bash
pre-commit install           # (First time only) Installs pre-commit hooks
pre-commit run --all-files   # Run all checks across the codebase
```

> **Tip:** This is the recommended first step before committing or pushing code.

---

### 2. ✅ Unit Tests with Coverage

Run the full test suite with code coverage reporting using pytest:

```bash
pytest --cov=govdocverify
```

* Replace `src` with your module's directory if different.
* Coverage results can be uploaded to Codecov or other CI tools.

---

### 3. 🔡 Spellchecking

Run [Codespell](https://github.com/codespell-project/codespell) to catch common typos in code, comments, and documentation:

```bash
codespell src tests docs
```

> **Note:** Codespell is also included in pre-commit, so this check runs automatically before each commit.

---

### 4. 📚 Docstring Formatting (Optional)

[docformatter](https://github.com/PyCQA/docformatter) ensures all Python docstrings follow [PEP 257](https://peps.python.org/pep-0257/) conventions.

```bash
docformatter -r src/
```

* Recommended for teams/projects that enforce strict docstring style.

---

### 5. 🛡️ Security Scanning

Run security scanners to identify vulnerabilities:

* **Bandit:** Scans Python source code for security issues

  ```bash
  bandit -r src -lll --skip B101
  ```

  * `-r src`: Recursively scans the `src` directory
  * `-lll`: Only high-severity issues
  * `--skip B101`: Skip assert statement warnings

* **pip-audit:** Checks installed dependencies for known security vulnerabilities

  ```bash
  pip-audit
  pip-audit -r requirements.txt
  ```

* **Safety (Optional):** Another dependency vulnerability scanner

  ```bash
  safety check
  ```

  * Not required if using pip-audit, but can be added for redundancy.

---

### 6. 🧬 Mutation Testing (Optional)

[Mutmut](https://mutmut.readthedocs.io/en/latest/) tests your suite’s effectiveness by making small code changes ("mutations") and checking if your tests catch them.

```bash
mutmut run --paths-to-mutate src
mutmut results
```

* Use this occasionally or in CI for robust projects.
* Mutation testing can be time-consuming.

---

### 7. 📦 Suggested Workflow

```bash
pre-commit run --all-files        # Lint, format, type check, spellcheck, markdown, security
pytest --cov=govdocverify         # Unit tests with coverage
bandit -r src -lll --skip B101    # Security scan (code)
pip-audit                         # Security scan (dependencies)
codespell src tests docs          # Spell check (if not running in pre-commit)
docformatter -r src/              # (Optional) Docstring formatting
mutmut run --paths-to-mutate src  # (Optional) Mutation testing
mutmut results
```

---

### 8. 📋 Quick Reference Table

| Tool         | Purpose                     | Command Example                               |
| ------------ | --------------------------- | --------------------------------------------- |
| Ruff         | Lint/format Python code     | `pre-commit run --all-files`                  |
| Black        | Code formatter              | `pre-commit run --all-files`                  |
| Mypy         | Static type checking        | `pre-commit run --all-files`                  |
| Bandit       | Security (code)             | `bandit -r src -lll --skip B101`              |
| pip-audit    | Security (dependencies)     | `pip-audit` / `pip-audit -r requirements.txt` |
| Codespell    | Spell check                 | `codespell src tests docs`                    |
| mdformat     | Markdown formatting/linting | `pre-commit run --all-files`                  |
| docformatter | Docstring style (optional)  | `docformatter -r src/`                        |
| Mutmut       | Mutation test (optional)    | `mutmut run --paths-to-mutate src`            |
| Pytest       | Unit tests/coverage         | `pytest --cov=govdocverify`                            |
| Safety       | Security (deps, optional)   | `safety check`                                |

---

## 📡 Direct API example

```bash
curl -F "doc_file=@mydoc.docx" -F "doc_type=Advisory Circular" \
  http://localhost:8000/process
```

## POST `/process` endpoint

Uploads a Word document and returns formatting results. The request must use
`multipart/form-data` and accepts these fields:

- `doc_file` – the `.docx` file to check.
- `doc_type` – type of document (e.g. `Advisory Circular`).
- `visibility_json` – optional JSON for per-check visibility.
- `group_by` – optional grouping mode (`category` or `severity`).

Example response:

```json
{
  "has_errors": true,
  "rendered": "<html>...",
  "by_category": {"format": []}
}
```

See [`docs/api-reference.md`](docs/api-reference.md) for the full reference.

---

### About the requirement files

`requirements.txt` & `requirements‑dev.txt` are generated for legacy tooling. `uv pip sync requirements-dev.txt` (or `pip install -e ".[dev]"`) remains the canonical path to an exact, up‑to‑date environment.

## License

This project is distributed under the [GNU General Public License v3.0](LICENSE).
