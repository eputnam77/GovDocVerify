import importlib
import importlib.util
from pathlib import Path

import pytest

# load src module for parity

def _load_src(module: str):
    base = Path(__file__).resolve().parents[1] / "src" / module
    spec = importlib.util.spec_from_file_location(module.replace("/", "."), base)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

models = importlib.import_module("govdocverify.models")
src_models = _load_src("govdocverify/models/__init__.py")

DocumentType = models.DocumentType
DocumentCheckResult = models.DocumentCheckResult
Severity = models.Severity
VisibilitySettings = models.VisibilitySettings

src_DocumentType = src_models.DocumentType
src_DocumentCheckResult = src_models.DocumentCheckResult
src_Severity = src_models.Severity
src_VisibilitySettings = src_models.VisibilitySettings


@pytest.mark.parametrize("mod_DocumentType", [DocumentType, src_DocumentType])
def test_document_type_from_string_handles_delimiters(mod_DocumentType):
    assert (
        mod_DocumentType.from_string("special-condition")
        == mod_DocumentType.SPECIAL_CONDITION
    )
    assert (
        mod_DocumentType.from_string("special_condition")
        == mod_DocumentType.SPECIAL_CONDITION
    )


@pytest.mark.parametrize(
    "DCR, Sev",
    [
        (DocumentCheckResult, Severity),
        (src_DocumentCheckResult, src_Severity),
    ],
)
def test_document_check_result_from_dict_accepts_string_severity(DCR, Sev):
    data = {
        "success": False,
        "severity": "warning",
        "issues": [
            {"message": "bad", "severity": "error", "category": "x"}
        ],
    }
    result = DCR.from_dict(data)
    assert result.severity == Sev.WARNING
    assert result.issues[0]["severity"] == Sev.ERROR


@pytest.mark.parametrize(
    "VS",
    [VisibilitySettings, src_VisibilitySettings],
)
def test_visibility_settings_from_dict_parses_string_booleans(VS):
    settings = VS.from_dict({"readability": "false", "analysis": "True", "version": 1})
    assert settings.show_readability is False
    assert settings.show_analysis is True
