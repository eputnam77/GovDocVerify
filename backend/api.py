import tempfile, os, logging
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app import process_document
from documentcheckertool.models import VisibilitySettings

log = logging.getLogger(__name__)

async def process_doc_endpoint(
    doc_file: UploadFile = File(...),
    doc_type: str        = Form(...),
    visibility_json: str = Form("{}"),
):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(await doc_file.read())
            tmp_path = tmp.name

        vis = VisibilitySettings.from_dict_json(visibility_json)
        html = process_document(tmp_path, doc_type, vis)

        return JSONResponse({"html": html})

    except Exception as e:
        log.exception("processing failed")
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)