import importlib.util
import pathlib
import zipfile


def load_src_export():
    module_path = pathlib.Path('src/govdocverify/export.py')
    spec = importlib.util.spec_from_file_location('export_src', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_save_results_docx_handles_unicode(tmp_path):
    export = load_src_export()
    path = tmp_path / 'result.docx'
    export.save_results_as_docx({'text': 'café'}, str(path))
    with zipfile.ZipFile(path) as zf:
        xml = zf.read('word/document.xml').decode('utf-8')
    assert 'café' in xml
