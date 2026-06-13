"""
Test Suite: covers pipeline TCs plus unit tests for matching algorithms.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestVideoProcessor(unittest.TestCase):

    def _make_frame(self, h=270, w=480, constant=100) -> np.ndarray:
        return np.full((h, w, 3), constant, dtype=np.uint8)

    def test_grid_difference_identical_frames_returns_false(self):
        from pipeline.video_processor import VideoProcessor
        vp = VideoProcessor("dummy.mp4")
        f  = np.random.randint(0, 255, (270, 480), dtype=np.uint8)
        self.assertFalse(vp.evaluate_scroll_state(f, f))

    def test_grid_difference_uniform_shift_detected(self):
        from pipeline.video_processor import VideoProcessor
        vp  = VideoProcessor("dummy.mp4")
        f1  = np.zeros((270, 480), dtype=np.uint8)
        f2  = np.full((270, 480), 50, dtype=np.uint8)
        self.assertTrue(vp.evaluate_scroll_state(f1, f2))

    def test_static_video_keeps_all_candidate_frames(self):
        from pipeline.video_processor import VideoProcessor

        fake_frames = [
            (True, np.full((270, 480, 3), 128, dtype=np.uint8)),
        ] * 10

        vp = VideoProcessor("static.mp4")
        with patch("cv2.VideoCapture") as mock_cap_cls:
            mock_cap = MagicMock()
            mock_cap_cls.return_value = mock_cap
            mock_cap.isOpened.return_value = True
            mock_cap.get.return_value      = 1.0

            side = fake_frames + [(False, None)]
            mock_cap.read.side_effect = [(r, f.copy() if f is not None else None)
                                          for r, f in side]
            results = vp.extract_candidate_frames()

        self.assertEqual(len(results), 10) 

    def test_corrupt_file_raises_io_error(self):
        from pipeline.video_processor import VideoProcessor
        vp = VideoProcessor("/nonexistent/file.mp4")
        with patch("cv2.VideoCapture") as mock_cap_cls:
            mock_cap = MagicMock()
            mock_cap_cls.return_value = mock_cap
            mock_cap.isOpened.return_value = False
            with self.assertRaises(IOError):
                vp.extract_candidate_frames()


class TestImageDeduplicator(unittest.TestCase):

    def _make_bgr(self, val=200, size=(100, 100)) -> np.ndarray:
        return np.full((*size, 3), val, dtype=np.uint8)

    def test_phash_returns_string(self):
        from pipeline.image_deduplicator import ImageDeduplicator
        d = ImageDeduplicator()
        h = d.calculate_phash(self._make_bgr(100))
        self.assertIsInstance(h, str)
        self.assertGreater(len(h), 0)

    def test_identical_frames_same_hash(self):
        from pipeline.image_deduplicator import ImageDeduplicator
        d  = ImageDeduplicator()
        f  = self._make_bgr(100)
        h1 = d.calculate_phash(f)
        h2 = d.calculate_phash(f.copy())
        self.assertEqual(h1, h2)

    def test_laplacian_variance_blurry_lt_sharp(self):
        from pipeline.image_deduplicator import ImageDeduplicator
        import cv2
        d     = ImageDeduplicator()
        sharp = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.rectangle(sharp, (50, 50), (150, 150), (255, 255, 255), 2)
        blurry = cv2.GaussianBlur(sharp, (21, 21), 0)
        self.assertGreater(
            d.calculate_laplacian_variance(sharp),
            d.calculate_laplacian_variance(blurry),
        )

    def test_cluster_duplicates_groups_identical(self):
        from pipeline.image_deduplicator import ImageDeduplicator
        d   = ImageDeduplicator()
        img = self._make_bgr(150)
        candidates = [
            {"frame": img.copy(), "timestamp_sec": float(i)}
            for i in range(5)
        ]
        clusters = d.cluster_duplicates(candidates)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]), 5)

    def test_select_sharpest_frame_picks_highest_variance(self):
        from pipeline.image_deduplicator import ImageDeduplicator
        import cv2
        d     = ImageDeduplicator()
        sharp = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.rectangle(sharp, (50, 50), (150, 150), (255, 255, 255), 2)
        blurry = cv2.GaussianBlur(sharp, (21, 21), 0)
        cluster = [
            {"frame": blurry, "timestamp_sec": 0.0},
            {"frame": sharp,  "timestamp_sec": 1.0},
        ]
        winner = d.select_sharpest_frame(cluster)
        self.assertEqual(winner["timestamp_sec"], 1.0)


class TestVectorStore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_upsert_and_query_above_cutoff(self):
        from db.vector_store import VectorStore, CONFIDENCE_CUTOFF
        vs = VectorStore(self.tmp)
        vec = [0.1] * 3072
        vs.upsert("v1", vec, "hello world", {"chunk_id": "c1"})
        results = vs.query(vec, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertGreaterEqual(results[0]["similarity"], CONFIDENCE_CUTOFF)

    def test_query_below_confidence_cutoff_returns_empty(self):
        from db.vector_store import VectorStore
        vs = VectorStore(self.tmp)
        stored = [1.0] + [0.0] * 3071
        query  = [0.0] * 3071 + [1.0]
        vs.upsert("v2", stored, "unrelated topic", {"chunk_id": "c2"})
        results = vs.query(query, top_k=1)
        self.assertEqual(results, [])


# ===========================================================================
# SourceMaterial entity validation tests
# ===========================================================================
class TestSourceMaterialValidation(unittest.TestCase):

    def test_valid_source_does_not_raise(self):
        from models.entities import SourceMaterial
        s = SourceMaterial(file_name="test.mp4", file_type="VIDEO",
                           storage_path="/tmp/test.mp4")
        s.validate() 

    def test_invalid_file_type_raises_value_error(self):
        from models.entities import SourceMaterial
        # Wrap in an assertion block so pytest knows this initialization must fail
        with self.assertRaises(ValueError):
            SourceMaterial(file_name="test.xyz", file_type="XYZ",
                           storage_path="/tmp/test.xyz")

    def test_empty_file_name_raises_value_error(self):
        from models.entities import SourceMaterial
        # Wrap in an assertion block so pytest knows this initialization must fail
        with self.assertRaises(ValueError):
            SourceMaterial(file_name="", file_type="PDF",
                           storage_path="/tmp/test.pdf")


class TestRepositories(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")

    def tearDown(self):
        if Path(self.tmp).exists():
            os.remove(self.tmp)

    def test_source_insert_and_retrieve(self):
        from db.repositories import Database, SourceRepository
        from models.entities import SourceMaterial
        db   = Database(self.tmp)
        repo = SourceRepository(db)
        src  = SourceMaterial(file_name="f.pdf", file_type="PDF",
                               storage_path="/tmp/f.pdf")
        repo.insert(src)
        fetched = repo.get(src.source_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.file_name, "f.pdf")

    def test_cascade_delete(self):
        from db.repositories import Database, SourceRepository, ChunkRepository
        from models.entities import SourceMaterial, DocumentChunk

        db       = Database(self.tmp)
        src_repo = SourceRepository(db)
        chk_repo = ChunkRepository(db)

        src   = SourceMaterial(file_name="x.txt", file_type="TEXT",
                                storage_path="/tmp/x.txt")
        src_repo.insert(src)
        chunk = DocumentChunk(source_id=src.source_id, vector_id="vec-001",
                               text_content="hello")
        chk_repo.insert(chunk)

        with db._conn() as conn:
            conn.execute("DELETE FROM sources WHERE source_id=?", (str(src.source_id),))

        remaining_chunks = chk_repo.get_by_source(src.source_id)
        self.assertEqual(remaining_chunks, [])


class TestGenerationEnginePrompt(unittest.TestCase):

    def test_no_context_returns_graceful_message(self):
        from pipeline.generation_engine import GenerationEngine
        with patch("openai.OpenAI"):
            engine = GenerationEngine("groq", "dummy-key")
        result = engine.generate_notes("some query", [])
        self.assertIn("No context available", result)

    def test_context_block_format(self):
        from pipeline.generation_engine import GenerationEngine
        sample = [
            {
                "text_content": "Deep learning is...",
                "metadata": {
                    "chunk_id":   "abc-123",
                    "local_path": "/assets/frame1.png",
                },
                "similarity": 0.85,
            }
        ]
        block = GenerationEngine._build_context_block(sample)
        self.assertIn("[Context ID: abc-123]", block)
        self.assertIn("[Associated Image Reference on Disk: /assets/frame1.png]", block)
        self.assertIn("Source Text: Deep learning is...", block)


if __name__ == "__main__":
    unittest.main(verbosity=2)