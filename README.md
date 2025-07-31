# GovDocVerify

FAA‑style validation for Word docs—CLI, FastAPI, and React UI in one toolkit.

**GovDocVerify** scans Advisory Circulars, Orders, and other FAA artifacts for headings, formatting, terminology, and accessibility issues. It delivers:

* a **FastAPI** backend (live Swagger UI)
* a modern **React/Next.js** frontend with real‑time preview
* an easy **CLI** for local batch checks

Full technical docs live under **`docs/`**; start with *docs/getting‑started.md* when you’re ready to dig deeper.

---

## ✨ Quick install (recommended)

We follow the same pattern as the other CLI projects: **pipx** for global tool shims, **uv** for ultra‑fast Python/venv work, and **Poetry ≥ 1.8** for deterministic installs.

```bash
# 0  One‑time per machine ───────────────────────────────────────────────
python3 -m pip install --user pipx                 # python -m pip install --user pipx
python3 -m pipx ensurepath                         # python -m pipx ensurepath (restart shell if PATH changed)

pipx install uv                                    # uv CLI & resolver
pipx install poetry                                # Poetry ≥1.8

# 1  Per project ────────────────────────────────────────────────────────
git clone https://github.com/eputnam77/GovDocVerify.git
cd GovDocVerify

# 2  Create & activate .venv (Python 3.13) ------------------------------
uv python install 3.13.0                           # downloads if missing
uv venv --python 3.13.0                            # writes .venv/ by default
source .venv/bin/activate                          # Windows: .venv\Scripts\activate

# 3  Install deps at uv speed ------------------------------------------------
poetry config installer.executable uv              # once per machine
poetry sync --with dev                             # mirrors poetry.lock + dev deps

pre-commit install                                 # Git hooks
```

---

## 🐍 Virtual‑env fallback (no uv)

```bash
python -m venv .venv
source .venv/bin/activate           # Win: .venv\Scripts\activate
pip install poetry
poetry install --with dev --sync    # --sync flag still works but is deprecated
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

## 🧪 Quality checks

```bash
pre-commit run --all-files
pytest --cov=src
```

---

## 📡 Direct API example

```bash
curl -F "doc_file=@mydoc.docx" -F "doc_type=Advisory Circular" \
  http://localhost:8000/process
```

---

### About the requirement files

`requirements.txt` & `requirements‑dev.txt` are generated for legacy tooling. `poetry sync` (or `pip install -e ".[dev]"`) remains the canonical path to an exact, up‑to‑date environment.
