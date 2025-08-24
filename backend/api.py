import asyncio
import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from contextlib import contextmanager
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
# after ``RESULT_TTL`` seconds to avoid unbounded growth. ``RESULT_TTL`` and the
# cleanup interval are configurable via environment variables to aid
# maintainability.
RESULT_TTL = int(os.getenv("RESULT_TTL", str(60 * 60)))  # default one hour
_CLEANUP_INTERVAL = int(os.getenv("RESULT_CLEANUP_INTERVAL", "60"))
_LAST_DISK_CLEANUP = 0.0
_RESULTS_DIR = Path(tempfile.gettempdir()) / "govdocverify_results"
_RESULTS_DIR.mkdir(exist_ok=True)
_RESULTS: dict[str, tuple[float, dict[str, Any]]] = {}
_RESULTS_LOCK = threading.Lock()
_ACTIVE_REQUESTS = 0
_ACTIVE_LOCK = threading.Lock()
_PROCESS_DELAY = float(os.getenv("PROCESS_DELAY", "0"))


def _cleanup_results(force: bool = False) -> None:
    """Remove expired cache entries and occasionally purge stale disk files."""
    now = time.time()
    with _RESULTS_LOCK:
        expired = [k for k, (ts, _) in _RESULTS.items() if now - ts > RESULT_TTL]
        for key in expired:
            _RESULTS.pop(key, None)
            file = _RESULTS_DIR / f"{key}.json"
            if file.exists():
                file.unlink()

    global _LAST_DISK_CLEANUP
    if not force and now - _LAST_DISK_CLEANUP < _CLEANUP_INTERVAL:
        return
    _LAST_DISK_CLEANUP = now
    for file in _RESULTS_DIR.glob("*.json"):
        if now - file.stat().st_mtime > RESULT_TTL:
            file.unlink()


def _save_result(result_id: str, data: dict[str, Any]) -> None:
    _cleanup_results()
    with _RESULTS_LOCK:
        _RESULTS[result_id] = (time.time(), data)
    path = _RESULTS_DIR / f"{result_id}.json"
    path.write_text(json.dumps(data))


def _load_result(result_id: str) -> dict[str, Any] | None:
    _cleanup_results()
    with _RESULTS_LOCK:
        cached = _RESULTS.get(result_id)
        if cached and time.time() - cached[0] <= RESULT_TTL:
            _RESULTS[result_id] = (time.time(), cached[1])
            return cached[1]
    path = _RESULTS_DIR / f"{result_id}.json"
    if path.exists() and time.time() - path.stat().st_mtime <= RESULT_TTL:
        data = json.loads(path.read_text())
        with _RESULTS_LOCK:
            _RESULTS[result_id] = (time.time(), data)
        return data
    return None


@contextmanager
def _track_request() -> Any:
    """Track the number of active requests."""
    global _ACTIVE_REQUESTS
    with _ACTIVE_LOCK:
        _ACTIVE_REQUESTS += 1
    try:
        yield
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE_REQUESTS -= 1


def wait_for_active_requests(timeout: float = 30.0) -> None:
    """Block until all active requests complete or timeout elapses."""
    start = time.time()
    while True:
        with _ACTIVE_LOCK:
            if _ACTIVE_REQUESTS == 0:
                return
        if time.time() - start > timeout:
            return
        time.sleep(0.05)


@rate_limit
async def process_doc_endpoint(
    doc_file: UploadFile = File(...),
    doc_type: str = Form(...),
    visibility_json: str = Form("{}"),
    group_by: str = Form("category"),
):
    tmp_path = None
    with _track_request():
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(await doc_file.read())
                tmp_path = tmp.name

            try:
                validate_file(tmp_path)
            except SecurityError as se:
                raise HTTPException(status_code=400, detail=str(se)) from se

            if _PROCESS_DELAY:
                await asyncio.sleep(_PROCESS_DELAY)

            try:
                json.loads(visibility_json)
            except json.JSONDecodeError as exc:  # invalid JSON should return 400
                raise HTTPException(status_code=400, detail="invalid visibility_json") from exc

            if group_by not in {"category", "severity"}:
                raise HTTPException(status_code=400, detail="invalid group_by")

            vis = VisibilitySettings.from_dict_json(visibility_json)
            result = process_document(tmp_path, doc_type, vis, group_by=group_by)

            if isinstance(result, dict):
                result_id = hashlib.sha256(
                    json.dumps(result, sort_keys=True).encode()
                ).hexdigest()
                _save_result(result_id, result)
                return JSONResponse(
                    {
                        "has_errors": result.get("has_errors", False),
                        "severity": result.get("severity"),
                        "rendered": result.get("rendered", ""),
                        "metadata": result.get("metadata", {}),
                        "by_category": result.get("by_category", {}),
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
