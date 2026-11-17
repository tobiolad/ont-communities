import hashlib
import json

from ont_pipeline.fetch import SourceSnapshot, save_snapshot


def make_snapshot(csv_bytes: bytes) -> SourceSnapshot:
    return SourceSnapshot(
        csv_bytes=csv_bytes,
        csv_text=csv_bytes.decode("utf-8-sig"),
        rows=[],
        resource_id="test-resource",
        download_url="https://example.com/test.csv",
        retrieved_at="2026-01-01T00:00:00+00:00",
        source_last_modified=None,
        file_hash=hashlib.md5(csv_bytes).hexdigest(),
        row_count=0,
        resource_name="Test Resource",
    )


class TestSaveSnapshot:
    def test_written_file_hash_matches_recorded_hash(self, tmp_path):
        """
        Regression test: save_snapshot must write the EXACT bytes that were
        hashed, not a re-decoded/re-encoded copy. A BOM-prefixed source
        (confirmed present in the real data) previously caused the archived
        file's own MD5 to differ from file_hash_md5 in its sidecar — the
        snapshot wasn't verifiable against its own recorded hash.
        """
        csv_bytes = b"\xef\xbb\xbfCategory,Project\nCommunities,Test Project\n"
        snapshot = make_snapshot(csv_bytes)

        csv_path, meta_path = save_snapshot(snapshot, raw_dir=tmp_path)

        written_bytes = csv_path.read_bytes()
        assert written_bytes == csv_bytes
        assert hashlib.md5(written_bytes).hexdigest() == snapshot.file_hash

        meta = json.loads(meta_path.read_text())
        assert meta["file_hash_md5"] == hashlib.md5(written_bytes).hexdigest()

    def test_bom_is_preserved_in_the_written_file(self, tmp_path):
        csv_bytes = "﻿Category,Project\n".encode("utf-8")
        snapshot = make_snapshot(csv_bytes)

        csv_path, _ = save_snapshot(snapshot, raw_dir=tmp_path)

        assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
