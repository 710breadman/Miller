import sys
from pathlib import Path

from PIL import Image

from miller.analysis import TesseractOcrAdapter


def test_tesseract_adapter_normalizes_tsv_from_fake_worker(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    Image.new("RGB", (200, 100), "white").save(image_path)
    worker = tmp_path / "fake_tesseract.py"
    worker.write_text(
        "import sys\n"
        "if '--version' in sys.argv:\n"
        "    print('tesseract 5.fixture')\n"
        "    raise SystemExit(0)\n"
        "print('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext')\n"
        "print('5\t1\t1\t1\t1\t1\t20\t10\t80\t20\t96\tHello')\n"
        "print('5\t1\t1\t1\t1\t2\t110\t10\t70\t20\t88\tworld')\n",
        encoding="utf-8",
    )
    adapter = TesseractOcrAdapter((sys.executable, str(worker)))
    result = adapter.recognize(image_path)
    assert result.engine_version == "tesseract 5.fixture"
    assert [span.text for span in result.spans] == ["Hello", "world"]
    assert result.spans[0].box.x == 0.1
    assert result.spans[0].confidence == 0.96
    assert result.spans[0].line_index == result.spans[1].line_index
