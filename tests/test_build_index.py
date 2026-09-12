import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from tools.build_index import CatalogError, check_index, render_index, write_index


class BuildIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.manifest_path = self.root / "sources" / "manifest.json"
        self.output_path = self.root / "INDEX.md"
        self.sources = [
            self._source("old", "Old title", "Old uploader", 65, "https://example.com/old"),
            self._source(
                "new",
                "新 [video]",
                "Maker *one*",
                5736,
                "https://example.com/watch?q=(new)",
            ),
        ]
        self._write_manifest()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _source(
        self, key: str, title: str, uploader: str, duration: float, url: str
    ) -> dict:
        lane = self.root / "sources" / key
        lane.mkdir(parents=True)
        (lane / "read.md").write_text("# Read\n", encoding="utf-8")
        metadata = {
            "id": f"source__{key}",
            "source": {"kind": "url", "value": url},
            "title": title,
            "uploader": uploader,
            "duration_seconds": duration,
        }
        (lane / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
        )
        return {
            "id": metadata["id"],
            "key": key,
            "path": key,
            "title": title,
            "duration_seconds": duration,
            "status": "ok",
            "artifacts": [
                {"kind": "metadata", "path": "metadata.json"},
                {"kind": "read", "path": "read.md"},
            ],
        }

    def _write_manifest(self, sources: list[dict] | None = None, schema: str = "5") -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": schema,
            "tool": "vctx",
            "status": "ok",
            "sources": self.sources if sources is None else sources,
        }
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )

    def test_renders_newest_first_with_safe_metadata(self) -> None:
        rendered = render_index(self.manifest_path)

        self.assertLess(rendered.index("新"), rendered.index("Old title"))
        self.assertIn(r"[新 \[video\]](sources/new/read.md)", rendered)
        self.assertIn(r"Maker \*one\*", rendered)
        self.assertIn("Duration: `01:35:36`", rendered)
        self.assertIn("q=%28new%29", rendered)
        self.assertEqual(rendered.count("Original video"), 2)
        self.assertTrue(rendered.endswith("\n"))

    def test_check_detects_stale_output_without_writing(self) -> None:
        self.output_path.write_text("stale\n", encoding="utf-8")

        self.assertFalse(check_index(self.manifest_path, self.output_path))
        self.assertEqual(self.output_path.read_text(encoding="utf-8"), "stale\n")

        self.output_path.write_bytes(render_index(self.manifest_path).encode("utf-8"))
        self.assertTrue(check_index(self.manifest_path, self.output_path))

        crlf = render_index(self.manifest_path).replace("\n", "\r\n").encode()
        self.output_path.write_bytes(crlf)
        self.assertFalse(check_index(self.manifest_path, self.output_path))

    def test_write_is_idempotent_and_leaves_no_temporary_file(self) -> None:
        write_index(self.manifest_path, self.output_path)
        first = self.output_path.read_bytes()

        write_index(self.manifest_path, self.output_path)

        self.assertEqual(self.output_path.read_bytes(), first)
        self.assertEqual({path.name for path in self.root.iterdir()}, {"sources", "INDEX.md"})

    def test_rejects_unsupported_schema(self) -> None:
        self._write_manifest(schema="6")

        with self.assertRaisesRegex(CatalogError, "schema"):
            render_index(self.manifest_path)

    def test_rejects_unsafe_lane_path(self) -> None:
        sources = deepcopy(self.sources)
        sources[0]["path"] = "../escape"
        self._write_manifest(sources)

        with self.assertRaisesRegex(CatalogError, "unsafe"):
            render_index(self.manifest_path)

    def test_rejects_incomplete_or_inconsistent_lane(self) -> None:
        sources = deepcopy(self.sources)
        sources[0]["status"] = "partial"
        self._write_manifest(sources)
        with self.assertRaisesRegex(CatalogError, "not ready"):
            render_index(self.manifest_path)

        self._write_manifest()
        metadata_path = self.root / "sources" / "old" / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["id"] = "different"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(CatalogError, "id"):
            render_index(self.manifest_path)

    def test_rejects_missing_read_artifact(self) -> None:
        (self.root / "sources" / "old" / "read.md").unlink()

        with self.assertRaisesRegex(CatalogError, "missing read artifact"):
            render_index(self.manifest_path)


if __name__ == "__main__":
    unittest.main()
