from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from app.core.omr_layouts import get_layout_provider


class OMREngineError(Exception):
    """Custom exception for errors during OMR processing."""

    pass


class OMREngine:
    @staticmethod
    def decode_image(image_bytes: bytes) -> np.ndarray:
        """Decodes raw image bytes into an OpenCV BGR image."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise OMREngineError(
                "Failed to decode image. File might be corrupted or in an unsupported format."
            )
        return img

    @classmethod
    def detect_anchors(cls, img: np.ndarray) -> List[Tuple[int, int]]:
        """
        Locates the four corner anchors in the raw image.
        Returns a list of (x, y) coordinates for [Top-Left, Top-Right, Bottom-Left, Bottom-Right].
        """
        h, w = img.shape[:2]

        # 1. Preprocess for contour detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Binary thresholding (adaptive or Otsu)
        thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # 2. Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for c in contours:
            area = cv2.contourArea(c)
            # Filter by area size (ignore noise and massive blocks)
            # Make threshold relative to image size for resolution independence
            img_area = h * w
            min_area = img_area * 0.00005  # ~150px on 3MP image
            max_area = img_area * 0.01  # ~30000px on 3MP image

            if area < min_area or area > max_area:
                continue

            perimeter = cv2.arcLength(c, True)
            if perimeter == 0:
                continue

            # Circularity metric: 4 * pi * Area / (Perimeter^2)
            circularity = 4 * np.pi * area / (perimeter**2)

            # Bounding box aspect ratio
            x, y, cw, ch = cv2.boundingRect(c)
            aspect_ratio = float(cw) / ch

            # Anchors are solid circles, so circularity should be close to 1.0, aspect ratio ~ 1.0
            if circularity >= 0.55 and 0.6 <= aspect_ratio <= 1.6:
                # Calculate center/centroid
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    candidates.append((cx, cy))

        if len(candidates) < 4:
            raise OMREngineError(
                f"Could not detect all 4 anchor marks. Found only {len(candidates)} candidates. "
                "Ensure the page corners are clearly visible and unblocked."
            )

        # 3. Classify candidates into 4 corners using distance metrics
        # Top-Left: minimizes cx + cy
        tl = min(candidates, key=lambda pt: pt[0] + pt[1])

        # Top-Right: minimizes (w - cx) + cy
        tr = min(candidates, key=lambda pt: (w - pt[0]) + pt[1])

        # Bottom-Left: minimizes cx + (h - cy)
        bl = min(candidates, key=lambda pt: pt[0] + (h - pt[1]))

        # Bottom-Right: minimizes (w - cx) + (h - cy)
        br = min(candidates, key=lambda pt: (w - pt[0]) + (h - pt[1]))

        # Check uniqueness of selected corners
        corners = [tl, tr, bl, br]
        if len(set(corners)) < 4:
            raise OMREngineError(
                "Overlapping corner anchor classification. "
                "Ensure the sheet is not extremely skewed or folded."
            )

        return corners

    @classmethod
    def align_image(cls, img: np.ndarray, anchors: List[Tuple[int, int]]) -> np.ndarray:
        """
        Warps the raw image using perspective transformation
        to output a standard 1000x1414 grayscale aligned image.
        """
        src_pts = np.array(anchors, dtype=np.float32)

        # Destination coordinates defined by our standard layout anchors in 1000x1414 space
        # [Top-Left, Top-Right, Bottom-Left, Bottom-Right]
        dst_pts = np.array(
            [[50.0, 50.0], [950.0, 50.0], [50.0, 1364.0], [950.0, 1364.0]], dtype=np.float32
        )

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        aligned = cv2.warpPerspective(img, M, (1000, 1414))

        # Convert aligned image to grayscale for subsequent threshold/fill analysis
        if len(aligned.shape) == 3:
            aligned = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)

        return aligned

    @classmethod
    def process_image(cls, image_bytes: bytes, layout_version: str) -> Dict[str, Any]:
        """
        Executes the entire OMR processing pipeline on raw image bytes.
        """
        img = cls.decode_image(image_bytes)
        anchors = cls.detect_anchors(img)
        aligned = cls.align_image(img, anchors)

        provider = get_layout_provider(layout_version)
        result = provider.detect(aligned)

        if not provider.validate(result):
            raise OMREngineError("Layout validation failed for detected data structure.")

        return result
