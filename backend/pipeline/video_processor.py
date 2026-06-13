"""
VideoProcessor
--------------
CPU-bound video frame filter with memory-safe execution.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)

TARGET_RESOLUTION = (480, 270)
TARGET_FPS        = 1
GRID_ROWS         = 3
GRID_COLS         = 3
SCROLL_THRESHOLD  = 15.0


class VideoProcessor:
    """Extracts high-value visual keyframes from a video file without memory bloat."""

    def __init__(
        self,
        video_path: str,
        target_fps: int = TARGET_FPS,
        target_resolution: tuple = TARGET_RESOLUTION,
    ):
        self.video_path        = video_path
        self.target_fps        = target_fps
        self.target_resolution = target_resolution

    def extract_candidate_frames(self) -> List[Dict]:
        """Returns structural frames mapped with precise timestamps."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {self.video_path}")

        native_fps: float = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_interval    = max(1, round(native_fps / self.target_fps))

        candidates: List[Dict] = []
        prev_gray:  Optional[np.ndarray] = None
        frame_idx   = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval != 0:
                    frame_idx += 1
                    continue

                timestamp = frame_idx / native_fps

                small = cv2.resize(
                    frame,
                    self.target_resolution,
                    interpolation=cv2.INTER_LINEAR,
                )
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                if prev_gray is not None:
                    is_scroll_active = self.evaluate_scroll_state(prev_gray, gray)
                    if is_scroll_active:
                        logger.debug("Scroll activity detected at %.2fs – frame suppressed.", timestamp)
                        prev_gray = gray
                        frame_idx += 1
                        continue

                candidates.append(
                    {
                        "timestamp_sec": timestamp,
                        "frame":         frame.copy(),  
                        "frame_index":   frame_idx,
                    }
                )
                prev_gray = gray
                frame_idx += 1

        finally:
            cap.release()

        logger.info("VideoProcessor: successfully extracted %d candidate frames.", len(candidates))
        return candidates

    def evaluate_scroll_state(self, f1: np.ndarray, f2: np.ndarray) -> bool:
        """Partition frames into a 3×3 grid to detect active layout scrolling."""
        h, w = f1.shape
        bh, bw = h // GRID_ROWS, w // GRID_COLS

        blocks_crossing_threshold = 0
        total_blocks = GRID_ROWS * GRID_COLS

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                y0, y1 = r * bh, (r + 1) * bh
                x0, x1 = c * bw, (c + 1) * bw
                
                block_diff = cv2.absdiff(f1[y0:y1, x0:x1], f2[y0:y1, x0:x1])
                if float(block_diff.mean()) > SCROLL_THRESHOLD:
                    blocks_crossing_threshold += 1

        return blocks_crossing_threshold >= (total_blocks - 2)