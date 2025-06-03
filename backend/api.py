import logging
import os
import tempfile

from fastapi import File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app import process_document
from documentcheckertool.models import VisibilitySettings

log = logging.getLogger(__name__)

async def process_doc_endpoint(
    doc_file: UploadFile = File(...),
    doc_type: str        = Form(...),
    visibility_json: str = Form("{}"),
    group_by: str        = Form("category"),
):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(await doc_file.read())
            tmp_path = tmp.name

        vis = VisibilitySettings.from_dict_json(visibility_json)
        html_result = process_document(tmp_path, doc_type, vis, group_by=group_by)

        # If process_document returns a dict (new structure), unpack it
        if isinstance(html_result, dict):
            return JSONResponse({
                "has_errors": html_result.get("has_errors", False),
                "rendered": html_result.get("rendered", ""),
                "by_category": html_result.get("by_category", {})
            })
        # Fallback for legacy string output
        return JSONResponse({"html": html_result})

    except Exception as e:
        log.exception("processing failed")
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
