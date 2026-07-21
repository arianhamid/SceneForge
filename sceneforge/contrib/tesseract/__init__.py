"""
SceneForge Tesseract Contrib Package

SceneForge's fifth real (non-stub) provider, and the first whose
positive-detection claim is actually verified in this environment
(not just its mechanics and negative path, unlike
`sceneforge.contrib.whisper`/`opencv`): Tesseract's trained language
data ships as a system package, so a real rendered-text image can be
generated and read back for real, with no network access needed.

The first real capability toward the "Facts" rung of the Understanding
Ladder (`docs/adr/0021-world-model-vocabulary.md`) -- recognized text
is objectively higher-level than a raw pixel region, the same way a
transcript segment is higher-level than an audio waveform.
"""

from sceneforge.contrib.tesseract.ocr_artifact import OCRTextArtifact
from sceneforge.contrib.tesseract.ocr_provider import TesseractOCRProvider

__all__ = ["OCRTextArtifact", "TesseractOCRProvider"]
