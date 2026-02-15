from __future__ import annotations

import unittest

from vibe_sentinel.gui import _content_type


class GuiStaticTests(unittest.TestCase):
    def test_content_types_for_core_assets(self) -> None:
        self.assertEqual(_content_type("/"), "text/html; charset=utf-8")
        self.assertEqual(_content_type("/index.html"), "text/html; charset=utf-8")
        self.assertEqual(_content_type("/artifacts.html"), "text/html; charset=utf-8")
        self.assertEqual(_content_type("/openclaw.html"), "text/html; charset=utf-8")
        self.assertEqual(_content_type("/tutorial.html"), "text/html; charset=utf-8")
        self.assertEqual(_content_type("/app.js"), "application/javascript; charset=utf-8")
        self.assertEqual(_content_type("/artifacts.js"), "application/javascript; charset=utf-8")
        self.assertEqual(_content_type("/openclaw.js"), "application/javascript; charset=utf-8")
        self.assertEqual(_content_type("/tutorial.js"), "application/javascript; charset=utf-8")
        self.assertEqual(_content_type("/fluid.js"), "application/javascript; charset=utf-8")
        self.assertEqual(_content_type("/styles.css"), "text/css; charset=utf-8")


if __name__ == "__main__":
    unittest.main()
