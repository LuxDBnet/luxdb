"""Pinned images and the one README logo block. All probe material is synthetic."""
import shutil
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_public import README_LOGO, README_LOGO_RENDERED, png_clean, scan, text_checks
from inventory import ASSETS, FILES


def chunk(kind, data):
    return len(data).to_bytes(4, "big") + kind + data + zlib.crc32(kind + data).to_bytes(4, "big")


def tiny_png(*extra):
    header = chunk(b"IHDR", (1).to_bytes(4, "big") * 2 + bytes([8, 0, 0, 0, 0]))
    body = chunk(b"IDAT", zlib.compress(b"\x00\x00"))
    return b"\x89PNG\r\n\x1a\n" + header + b"".join(extra) + body + chunk(b"IEND", b"")


class PinnedAssets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.copy = Path(self.temp.name) / "candidate"
        for rel in FILES:
            target = self.copy / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, target)
        self.baseline = set(scan(self.copy))

    def new(self):
        return {(f.category, f.path) for f in set(scan(self.copy)) - self.baseline}

    def test_pinned_images_pass_as_committed(self):
        self.assertFalse({f for f in self.baseline if f.path in ASSETS or f.category in {"asset-drift", "embedded-media", "non-text-file"}})

    def test_one_changed_byte_blocks(self):
        target = self.copy / "assets/mark-light.png"
        raw = bytearray(target.read_bytes())
        raw[-20] ^= 1
        target.write_bytes(bytes(raw))
        self.assertIn(("asset-drift", "assets/mark-light.png"), self.new())

    def test_another_image_swapped_in_blocks(self):
        shutil.copyfile(ROOT / "assets/mark-dark.png", self.copy / "assets/mark-light.png")
        self.assertIn(("asset-drift", "assets/mark-light.png"), self.new())

    def test_extra_image_blocks(self):
        (self.copy / "assets/extra.png").write_bytes(tiny_png())
        self.assertIn(("unapproved-file", "<unapproved path>"), self.new())

    def test_text_chunks_fail_the_png_check(self):
        self.assertTrue(png_clean(tiny_png()))
        for kind in (b"tEXt", b"iTXt", b"zTXt", b"eXIf", b"tIME"):
            self.assertFalse(png_clean(tiny_png(chunk(kind, b"Comment\x00synthetic"))), kind)
        self.assertFalse(png_clean(tiny_png() + b"trailing"))
        self.assertFalse(png_clean(b"GIF89a"))

    def test_img_elsewhere_blocks(self):
        for path in ("NOTICE.md", "docs/quickstart.md"):
            self.assertIn("embedded-media", text_checks('<img src="assets/mark-light.png" alt="LuxDB">', path), path)
        self.assertIn("embedded-media", text_checks(README_LOGO, "NOTICE.md"))

    def test_edited_logo_block_blocks(self):
        for edited in (README_LOGO_RENDERED.replace('alt="LuxDB"', 'alt="LuxDB" onerror="x"'),
                       README_LOGO_RENDERED.replace("assets/mark-dark.png", "assets/extra.png"),
                       README_LOGO, " " + README_LOGO_RENDERED):
            self.assertIn("embedded-media", text_checks(edited + "# LuxDB\n", "README.md"))

    def test_second_logo_block_blocks(self):
        self.assertNotIn("embedded-media", text_checks(README_LOGO_RENDERED + "# LuxDB\n", "README.md"))
        self.assertNotIn("embedded-media", text_checks(README_LOGO + "# {{PROJECT_NAME}}\n", "templates/README.md.in"))
        self.assertIn("embedded-media", text_checks(README_LOGO_RENDERED + "# LuxDB\n\n" + README_LOGO_RENDERED, "README.md"))
        self.assertIn("embedded-media", text_checks(README_LOGO_RENDERED + '<img src="assets/og-1200x630.png">\n', "README.md"))

    def test_scanner_source_holds_only_the_one_constant(self):
        source = (ROOT / "tools/check_public.py").read_text()
        self.assertNotIn("embedded-media", text_checks(source, "tools/check_public.py"))
        self.assertIn("embedded-media", text_checks(source + '\nEXTRA = "<img src=x>"\n', "tools/check_public.py"))
        self.assertIn("embedded-media", text_checks(source + "\n" + README_LOGO, "tools/check_public.py"))

    def test_inventory_digest_exemption_is_exact_pin_lines(self):
        digest = ASSETS["assets/mark-light.png"]
        with (self.copy / "tools/inventory.py").open("a") as stream:
            stream.write(f'\nSYNTHETIC_TOKEN = "{digest}"\n')
        self.assertIn(("high-entropy-secret", "tools/inventory.py"), self.new())


if __name__ == "__main__":
    unittest.main()
