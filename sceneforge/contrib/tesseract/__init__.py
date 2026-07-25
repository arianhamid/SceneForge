"""
SceneForge Tesseract Contrib Package

SceneForge's fifth real (non-stub) provider, and the first whose
positive-detection claim is actually verified in this environment
(not just its mechanics and negative path, unlike
`sceneforge.contrib.whisper`/`opencv`): Tesseract's trained language
data ships as a system package, so a real rendered-text image can be
generated and read back for real, with no network access needed.

The second real capability at the Evidence rung to be organized by a
cross-domain Knowledge Builder (`SceneTextBuilder`, correlating OCR
text back to scenes the same way `SceneFaceBuilder` correlates faces —
`docs/adr/0016-cross-domain-knowledge-builder.md`). Recognized text is
objectively higher-level than a raw pixel region, but per
`docs/adr/0022-real-ocr-provider.md`'s explicit framing ("Still
Evidence Not Facts" is literally that ADR's title), it does not by
itself reach the "Facts" rung of the Understanding Ladder
(`docs/adr/0021-world-model-vocabulary.md`) -- a sign reading "POLICE"
becoming the Fact "this location is a police station" needs a
semantic interpretation step this package does not attempt.
`sceneforge.contrib.transformers_caption` and
`sceneforge.contrib.transformers_object_detection` are the providers
that actually reach Facts (via `FactExtractionBuilder`).
"""

from sceneforge.contrib.tesseract.ocr_artifact import OCRTextArtifact
from sceneforge.contrib.tesseract.ocr_provider import TesseractOCRProvider

__all__ = ["OCRTextArtifact", "TesseractOCRProvider"]
