import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from collections import Counter

import cv2
import numpy as np
import pytesseract
import re
import math


# Lightweight configuration via environment variables
OCR_MIN_CONF = float(os.getenv("OCR_MIN_CONF", "0.5"))
STEGO_ENTROPY_THRESH = float(os.getenv("STEGO_ENTROPY_THRESH", "7.5"))
STEGO_LSB_MIN = float(os.getenv("STEGO_LSB_MIN", "0.45"))
STEGO_LSB_MAX = float(os.getenv("STEGO_LSB_MAX", "0.55"))


class OCRDetector:
    """Detects sensitive text in screenshots using OCR with per-word confidence."""

    SENSITIVE_KEYWORDS = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "api_key",
        "apikey",
        "api-key",
        "private_key",
        "private key",
        "privatekey",
        "access_token",
        "auth_token",
        "token",
        "credentials",
        "credential",
        "confidential",
        "sensitive",
    ]

    PATTERNS: Dict[str, str] = {
        "credit_card": r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    }

    def __init__(self, min_confidence: float | None = None) -> None:
        self.min_confidence = float(min_confidence) if min_confidence is not None else OCR_MIN_CONF
        self.logger = logging.getLogger("visual_ocr")

    def preprocess_image(self, image_path: str) -> np.ndarray:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        if width < 300:
            scale = 300 / float(width)
            new_width = 300
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height))

        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def extract_text_with_confidence(self, processed_image: np.ndarray) -> Tuple[str, float]:
        try:
            data = pytesseract.image_to_data(
                processed_image,
                output_type=pytesseract.Output.DICT,
                config="--oem 3 --psm 6",
            )
            words: List[str] = []
            confidences: List[int] = []

            for i, word in enumerate(data.get("text", [])):
                if word.strip():
                    words.append(word)
                    conf = data.get("conf", [])[i]
                    if conf != -1:
                        confidences.append(int(conf))

            full_text = " ".join(words)
            if confidences:
                avg_conf = sum(confidences) / float(len(confidences)) / 100.0
            else:
                avg_conf = 0.0
            return full_text, avg_conf
        except Exception as exc:
            self.logger.error("OCR failed: %s", exc)
            return "", 0.0

    def detect_keywords(self, text: str) -> List[str]:
        text_lower = text.lower()
        return [kw for kw in self.SENSITIVE_KEYWORDS if kw in text_lower]

    def detect_patterns(self, text: str) -> Dict[str, List[str]]:
        results: Dict[str, List[str]] = {}
        for name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                results[name] = matches
        return results

    def calculate_detection_confidence(
        self,
        keywords: List[str],
        patterns: Dict[str, List[str]],
        ocr_confidence: float,
    ) -> float:
        base_score = 0.0
        if keywords:
            base_score += min(len(keywords) * 0.2, 0.6)
        if patterns:
            base_score += min(len(patterns) * 0.3, 0.4)
        final_score = base_score * max(0.0, min(ocr_confidence, 1.0))
        return min(final_score, 1.0)

    def process(self, session_id: str, image_path: str) -> Dict[str, object]:
        start_time = time.time()
        # Only attempt OCR on common image extensions
        if not image_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            return {"detected": False, "skipped": True, "reason": "not_image"}

        try:
            processed = self.preprocess_image(image_path)
            text, ocr_conf = self.extract_text_with_confidence(processed)
            duration = time.time() - start_time

            if not text.strip():
                self.logger.debug("No text detected in %.3fs", duration)
                return {"detected": False}

            if ocr_conf < self.min_confidence:
                self.logger.debug("OCR confidence too low: %.2f", ocr_conf)
                return {"detected": False, "low_confidence": True}

            keywords = self.detect_keywords(text)
            patterns = self.detect_patterns(text)

            if keywords or patterns:
                confidence = self.calculate_detection_confidence(keywords, patterns, ocr_conf)
                self.logger.info(
                    "OCR detection: conf=%.2f ocr_conf=%.2f time=%.3fs keywords=%d patterns=%d",
                    confidence,
                    ocr_conf,
                    duration,
                    len(keywords),
                    len(patterns),
                )
                return {
                    "detected": True,
                    "keywords": keywords,
                    "patterns": patterns,
                    "confidence": confidence,
                    "ocr_confidence": ocr_conf,
                    "text_preview": text[:200],
                    "processing_time": duration,
                    "image_path": image_path,
                    "session_id": session_id,
                }

            self.logger.debug("No sensitive content, time=%.3fs", duration)
            return {"detected": False}
        except Exception as exc:
            self.logger.error("OCR processing failed: %s", exc)
            return {"detected": False, "error": str(exc)}


class StegoDetector:
    """Detects steganography attempts in images with configurable thresholds."""

    def __init__(
        self,
        entropy_threshold: float | None = None,
        lsb_min: float | None = None,
        lsb_max: float | None = None,
    ) -> None:
        self.entropy_threshold = float(entropy_threshold) if entropy_threshold is not None else STEGO_ENTROPY_THRESH
        self.lsb_min = float(lsb_min) if lsb_min is not None else STEGO_LSB_MIN
        self.lsb_max = float(lsb_max) if lsb_max is not None else STEGO_LSB_MAX
        self.logger = logging.getLogger("visual_stego")

    def calculate_entropy(self, image: np.ndarray) -> float:
        pixels = image.flatten()
        counter = Counter(pixels)
        total_pixels = float(len(pixels)) or 1.0
        entropy = 0.0
        for count in counter.values():
            probability = count / total_pixels
            if probability > 0.0:
                entropy -= probability * math.log2(probability)
        return entropy

    def extract_lsb_plane(self, image: np.ndarray) -> np.ndarray:
        return image & 1

    def analyze_lsb_distribution(self, lsb_plane: np.ndarray) -> Tuple[float, bool]:
        total_bits = float(lsb_plane.size) or 1.0
        ones = float(np.sum(lsb_plane))
        ratio_ones = ones / total_bits
        is_suspicious = ratio_ones < self.lsb_min or ratio_ones > self.lsb_max
        return ratio_ones, is_suspicious

    def detect_stego(self, image_path: str) -> Dict[str, object]:
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return {"suspicious": False, "error": "Failed to load image"}

            entropy = self.calculate_entropy(img)
            entropy_suspicious = entropy > self.entropy_threshold

            lsb_plane = self.extract_lsb_plane(img)
            lsb_ratio, lsb_suspicious = self.analyze_lsb_distribution(lsb_plane)

            is_suspicious = bool(entropy_suspicious or lsb_suspicious)
            confidence = 0.0
            if entropy_suspicious:
                confidence += 0.5
            if lsb_suspicious:
                confidence += 0.3

            return {
                "suspicious": is_suspicious,
                "entropy": entropy,
                "entropy_suspicious": entropy_suspicious,
                "lsb_ratio": lsb_ratio,
                "lsb_suspicious": lsb_suspicious,
                "confidence": min(confidence, 1.0),
            }
        except Exception as exc:
            self.logger.error("Stego detection failed: %s", exc)
            return {"suspicious": False, "error": str(exc)}

    def process(self, session_id: str, image_path: str) -> Dict[str, object]:
        start_time = time.time()
        if not image_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            return {"suspicious": False, "skipped": True, "reason": "not_image"}

        result = self.detect_stego(image_path)
        duration = time.time() - start_time

        if result.get("suspicious"):
            self.logger.info(
                "Stego detection: conf=%.2f entropy=%.2f lsb=%.2f time=%.3fs",
                result.get("confidence", 0.0),
                result.get("entropy", 0.0),
                result.get("lsb_ratio", 0.0),
                duration,
            )
        else:
            self.logger.debug("No stego detected, time=%.3fs", duration)

        result.update({
            "image_path": image_path,
            "session_id": session_id,
            "processing_time": duration,
        })
        return result
