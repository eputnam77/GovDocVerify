import logging
import os
import tempfile
import uuid
from typing import Any

from fastapi import BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from govdocverify import export
from govdocverify.cli import process_document
from govdocverify.models import VisibilitySettings
from govdocverify.utils.security import SecurityError, rate_limit, validate_file

log = logging.getLogger(__name__)

_RESULTS: dict[str, dict[str, Any]] = {}


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
            result_id = uuid.uuid4().hex
            _RESULTS[result_id] = result.get("by_category", {})
            return JSONResponse(
                {
                    "has_errors": result.get("has_errors", False),
                    "rendered": result.get("rendered", ""),
                    "by_category": result.get("by_category", {}),
                    "result_id": result_id,
                }
            )
        result_id = uuid.uuid4().hex
        _RESULTS[result_id] = {"html": result}
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
    data = _RESULTS.get(result_id)
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
