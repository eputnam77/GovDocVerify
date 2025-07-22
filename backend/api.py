import logging
import os
import tempfile

from fastapi import File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from govdocverify.cli import process_document
from govdocverify.models import VisibilitySettings
from govdocverify.utils.security import SecurityError, rate_limit, validate_file

log = logging.getLogger(__name__)


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
        html_result = process_document(tmp_path, doc_type, vis, group_by=group_by)

        # If process_document returns a dict (new structure), unpack it
        if isinstance(html_result, dict):
            return JSONResponse(
                {
                    "has_errors": html_result.get("has_errors", False),
                    "rendered": html_result.get("rendered", ""),
                    "by_category": html_result.get("by_category", {}),
                }
            )
        # Fallback for legacy string output
        return JSONResponse({"html": html_result})

    except HTTPException:
        raise
    except Exception as e:
        log.exception("processing failed")
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
