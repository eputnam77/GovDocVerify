import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from govdocverify import export
from govdocverify.cli import process_document
from govdocverify.models import VisibilitySettings
from govdocverify.utils.security import SecurityError, rate_limit, validate_file

log = logging.getLogger(__name__)

# Results are cached in memory for quick access but also written to disk so that
# workers in a multi-process deployment can retrieve them. Each entry expires
# after ``RESULT_TTL`` seconds to avoid unbounded growth.
RESULT_TTL = 60 * 60  # one hour
_RESULTS_DIR = Path(tempfile.gettempdir()) / "govdocverify_results"
_RESULTS_DIR.mkdir(exist_ok=True)
_RESULTS: dict[str, tuple[float, dict[str, Any]]] = {}


def _cleanup_results() -> None:
    """Remove expired cache entries and stray files on disk."""
    now = time.time()
    expired = [k for k, (ts, _) in _RESULTS.items() if now - ts > RESULT_TTL]
    for key in expired:
        _RESULTS.pop(key, None)
        file = _RESULTS_DIR / f"{key}.json"
        if file.exists():
            file.unlink()
    for file in _RESULTS_DIR.glob("*.json"):
        if now - file.stat().st_mtime > RESULT_TTL:
            file.unlink()


def _save_result(result_id: str, data: dict[str, Any]) -> None:
    _cleanup_results()
    _RESULTS[result_id] = (time.time(), data)
    path = _RESULTS_DIR / f"{result_id}.json"
    path.write_text(json.dumps(data))


def _load_result(result_id: str) -> dict[str, Any] | None:
    _cleanup_results()
    cached = _RESULTS.get(result_id)
    if cached:
        _RESULTS[result_id] = (time.time(), cached[1])
        return cached[1]
    path = _RESULTS_DIR / f"{result_id}.json"
    if path.exists():
        data = json.loads(path.read_text())
        _RESULTS[result_id] = (time.time(), data)
        return data
    return None


@rate_limit
async def process_doc_endpoint(
    doc_file: UploadFile = File(...),
    doc_type: str = Form(...),
    visibility_json: str = Form("{}"),
    group_by: str = Form("category"),
):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(await doc_file.read())
            tmp_path = tmp.name

        try:
            validate_file(tmp_path)
        except SecurityError as se:
            raise HTTPException(status_code=400, detail=str(se)) from se

        vis = VisibilitySettings.from_dict_json(visibility_json)
        result = process_document(tmp_path, doc_type, vis, group_by=group_by)

        if isinstance(result, dict):
            data = result.get("by_category", {})
            result_id = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
            _save_result(result_id, data)
            return JSONResponse(
                {
                    "has_errors": result.get("has_errors", False),
                    "rendered": result.get("rendered", ""),
                    "by_category": data,
                    "result_id": result_id,
                }
            )
        data = {"html": result}
        result_id = hashlib.sha256(result.encode()).hexdigest()
        _save_result(result_id, data)
        return JSONResponse({"html": result, "result_id": result_id})

    except HTTPException:
        raise
    except Exception as e:
        log.exception("processing failed")
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def download_result(result_id: str, fmt: str, background: BackgroundTasks) -> FileResponse:
    data = _load_result(result_id)
    if data is None:
        raise HTTPException(status_code=404, detail="result not found")
    suffix = f".{fmt}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        path = tmp.name
    if fmt == "docx":
        export.save_results_as_docx(data, path)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif fmt == "pdf":
        export.save_results_as_pdf(data, path)
        media = "application/pdf"
    else:
        raise HTTPException(status_code=400, detail="unsupported format")
    background.add_task(os.unlink, path)
    return FileResponse(path, media_type=media, filename=f"results{suffix}", background=background)
