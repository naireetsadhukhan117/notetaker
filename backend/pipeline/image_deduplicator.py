"""
ImageDeduplicator
-----------------
RAM-bound clustering & sharpest-frame selection.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

logger = logging.getLogger(__name__)

HAMMING_THRESHOLD = 4


def _compute_phash_cv2(image: np.ndarray) -> str:
    """True Perceptual Hash (pHash) using Discrete Cosine Transform (DCT)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    
    img_float = np.float32(resized)
    dct = cv2.dct(img_float)
    dct_low = dct[0:8, 0:8]
    
    median = np.median(dct_low)
    bits = (dct_low > median).flatten()
    
    hex_str = ""
    for i in range(0, 64, 4):
        nibble = bits[i:i+4]
        val = (nibble * np.array([8, 4, 2, 1])).sum()
        hex_str += f"{val:x}"
        
    return hex_str


def _hamming_distance(h1: str, h2: str) -> int:
    if len(h1) != len(h2):
        return max(len(h1), len(h2)) * 4
    dist = 0
    for a, b in zip(h1, h2):
        xor = int(a, 16) ^ int(b, 16)
        dist += bin(xor).count("1")
    return dist


class ImageDeduplicator:
    """Groups visually identical frames and keeps only the sharpest instance."""

    def __init__(self, hamming_threshold: int = HAMMING_THRESHOLD):
        self.hamming_threshold = hamming_threshold

    def calculate_phash(self, image: np.ndarray) -> str:
        return _compute_phash_cv2(image)

    def cluster_duplicates(self, candidates: List[Dict]) -> List[List[Dict]]:
        if not candidates:
            return []

        for c in candidates:
            if "phash" not in c:
                c["phash"] = self.calculate_phash(c["frame"])

        clusters: List[List[Dict]] = []
        unassigned = list(candidates)

        while unassigned:
            seed = unassigned.pop(0)
            cluster = [seed]
            remaining = []
            
            for candidate in unassigned:
                d = _hamming_distance(seed["phash"], candidate["phash"])
                if d <= self.hamming_threshold:
                    cluster.append(candidate)
                else:
                    remaining.append(candidate)
                    
            clusters.append(cluster)
            unassigned = remaining

        return clusters

    def select_sharpest_frame(self, cluster: List[Dict]) -> Dict:
        for item in cluster:
            if "sharpness_score" not in item:
                item["sharpness_score"] = self.calculate_laplacian_variance(item["frame"])
        return max(cluster, key=lambda x: x["sharpness_score"])

    def calculate_laplacian_variance(self, image: np.ndarray) -> float:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def persist_best_frames(self, clusters: List[List[Dict]], asset_dir: str) -> List[Dict]:
        """Saves the sharpest cluster images and purges raw pixel matrices from memory."""
        Path(asset_dir).mkdir(parents=True, exist_ok=True)
        winners: List[Dict] = []

        for cluster in clusters:
            if not cluster:
                continue
                
            winner = self.select_sharpest_frame(cluster)
            img_name = f"{uuid.uuid4().hex}.png"
            out_path = str(Path(asset_dir) / img_name)
            
            cv2.imwrite(out_path, winner["frame"])
            winner["local_path"] = out_path
            winners.append(winner)

            for item in cluster:
                if "frame" in item:
                    del item["frame"]

        return winners