"""
Integration tests for Pipeline workflow.
"""

from sceneforge.contrib.identity import IdentityProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.image import ImageMedia
from sceneforge.media.video import VideoMedia
from sceneforge.media.audio import AudioMedia


def test_pipeline_image_workflow():
    """Test complete image processing workflow."""
    # Create media
    image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")
    
    # Create pipeline
    pipeline = Pipeline(provider=IdentityProvider())
    
    # Process
    artifacts = list(pipeline.run(image))
    
    # Verify
    assert len(artifacts) == 1
    assert artifacts[0].provider == "identity"
    assert artifacts[0].media_id == image.id


def test_pipeline_video_workflow():
    """Test complete video processing workflow."""
    # Create media
    video = VideoMedia(
        name="movie.mp4",
        duration=120.0,
        codec="h264",
        fps=30.0
    )
    
    # Create pipeline
    pipeline = Pipeline(provider=IdentityProvider())
    
    # Process
    artifacts = list(pipeline.run(video))
    
    # Verify
    assert len(artifacts) == 1
    assert artifacts[0].provider == "identity"


def test_pipeline_audio_workflow():
    """Test complete audio processing workflow."""
    # Create media
    audio = AudioMedia(
        name="sound.wav",
        duration=30.0,
        sample_rate=44100,
        channels=2
    )
    
    # Create pipeline
    pipeline = Pipeline(provider=IdentityProvider())
    
    # Process
    artifacts = list(pipeline.run(audio))
    
    # Verify
    assert len(artifacts) == 1
    assert artifacts[0].provider == "identity"