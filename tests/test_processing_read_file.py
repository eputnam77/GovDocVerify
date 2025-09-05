from govdocverify.processing import _read_file_content


def test_read_file_content_latin1(tmp_path):
    path = tmp_path / 'latin1.txt'
    path.write_bytes('café'.encode('latin-1'))
    assert _read_file_content(str(path)) == 'café'
