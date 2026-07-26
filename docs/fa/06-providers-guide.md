<style>
:root {
  direction: rtl;
  text-align: right;
}
code, pre {
  direction: ltr;
  text-align: left;
}
</style>

# ۶. راهنمای هفت Provider قابلیت‌محور پروژه

تا امروز، هفت Provider واقعیِ قابلیت‌محور (نه ساختگی) در پروژه وجود دارد. Providerهای ابزاری مثل `MediaHashProvider` جدا از این شمارش‌اند. هرکدام از این هفت مورد یک الگوی متفاوت برای «از کجا مدل/ابزارش را می‌آورد» دارند — و این تفاوت، درسی مهم درباره‌ی طراحی پروژه است.

## جدول کلی

| Provider                              | قابلیت             | ابزار پشت‌صحنه                                                | نیاز به دانلود وزن مدل؟                 |
| ------------------------------------- | ------------------ | ------------------------------------------------------------- | --------------------------------------- |
| `FFmpegFrameExtractionProvider`       | `FRAME_EXTRACTION` | دستور خط‌فرمان `ffmpeg`                                       | خیر                                     |
| `PySceneDetectProvider`               | `DETECT_SCENES`    | کتابخانه‌ی `scenedetect` (الگوریتمی)                          | خیر                                     |
| `WhisperTranscribeProvider`           | `TRANSCRIBE`       | کتابخانه‌ی `faster-whisper`                                   | **بله**                                 |
| `OpenCVFaceDetectionProvider`         | `FACE_DETECTION`   | Haar Cascade در `opencv`                                      | خیر (وزن‌ها همراه پکیج نصب می‌شوند)     |
| `TesseractOCRProvider`                | `OCR`              | موتور `tesseract-ocr`                                         | خیر (داده‌ی زبان همراه پکیج نصب می‌شود) |
| `TransformersCaptionProvider`         | `CAPTION`          | یک pipeline تزریق‌شده‌ی `transformers` (`image-text-to-text`) | **بله** (این محیط دسترسی به آن ندارد)   |
| `TransformersObjectDetectionProvider` | `OBJECT_DETECTION` | یک pipeline تزریق‌شده‌ی `transformers` (`object-detection`)   | **بله** (این محیط دسترسی به آن ندارد)   |

## نکته‌ی مهم: «مدل‌محور بودن» به معنی «نیاز به دانلود» نیست

قبلاً فرض بر این بود که هر Providerِ مدل‌محور، باید مدلش را «تزریق» (inject) کند — یعنی به‌جای ساختن مدل داخل خودِ Provider، مدل را از بیرون بگیرد (دلیلش در بخش بعد است). اما وقتی `OpenCVFaceDetectionProvider` ساخته شد، این فرض چک شد و نادرست بود: وزن‌های Haar Cascade همراه خودِ پکیج `opencv-python` نصب می‌شوند — نیازی به دانلود جداگانه یا اینترنت نیست. همین اتفاق برای `TesseractOCRProvider` هم افتاد: داده‌ی زبان انگلیسی همراه پکیج سیستمی `tesseract-ocr` نصب می‌شود.

پس قانون واقعی این است: **قبل از فرض کردن که یک Provider نیاز به تزریق مدل دارد، چک کن که آیا وزن‌ها همراه خودِ کتابخانه می‌آیند یا نه.**

## چرا `WhisperTranscribeProvider` فرق دارد؟ (تزریق وابستگی)

```python
class WhisperTranscribeProvider(Provider):
    def __init__(self, model: WhisperModelProtocol, **transcribe_kwargs):
        self._model = model
```

اینجا مدل به‌عنوان یک پارامتر گرفته می‌شود، نه این‌که خودِ Provider آن را بسازد. دلیل: ساختن یک `WhisperModel` واقعی، وزن‌های مدل را از سرور Hugging Face دانلود می‌کند. این یعنی:

- بدون اینترنت، حتی نمی‌توانی این Provider را تست کنی.
- ساختن مدل کند است و به GPU نیاز دارد.

با تزریق، در تست‌ها می‌توانیم یک «مدل ساختگی» (fake model) بسازیم که همان شکل (Protocol) را دارد اما هیچ وزن واقعی‌ای بار نمی‌کند:

```python
class FakeWhisperModel:
    def transcribe(self, audio, **kwargs):
        return iter([FakeSegment(0.0, 2.0, "سلام")]), FakeInfo()


provider = WhisperTranscribeProvider(FakeWhisperModel())
```

این یعنی می‌توانیم منطق داخلی Provider (مثل «هر سگمنت را چطور به Artifact تبدیل کن») را کامل تست کنیم، بدون هیچ وابستگی به اینترنت یا GPU.

## دومین الگوی تزریق وابستگی: `TransformersCaptionProvider`

همان الگوی `WhisperTranscribeProvider` (تزریق مدل، نه ساختنش داخل Provider) دوباره برای دو Provider جدید استفاده شد — این‌بار برای رسیدن به لایه‌ی «حقایق» (Facts):

```python
class TransformersCaptionProvider(Provider):
    def __init__(self, pipe: ImageTextToTextPipelineProtocol) -> None:
        self._pipe = pipe
```

نکته‌ی طراحی مهم: این Provider فقط `ImageMedia` قبول می‌کند، نه `VideoMedia` — با این‌که `Capability.CAPTION` برای هر دو ثبت شده. دلیلش این است که «توضیح‌دادن کل یک ویدیو» نیاز به یک تصمیم دارد («کدام قاب یا قاب‌ها را توضیح بدهم؟») که این Provider عمداً نمی‌گیرد؛ آن تصمیم را به‌جای این‌که خودش حدس بزند، به لایه‌ای که قاب‌ها را استخراج می‌کند (`sceneforge.contrib.ffmpeg`) واگذار می‌کند.

`TransformersObjectDetectionProvider` هم دقیقاً همین الگو را برای `Capability.OBJECT_DETECTION` تکرار می‌کند.

### یک باگ واقعی که هنگام نوشتن این دو Provider پیدا شد

`FaceDetectionArtifact` و `OCRTextArtifact` از قبل فیلد `source_frame_path` را داشتند (برای تطبیق با صحنه، طبق الگویی که پایین‌تر توضیح می‌دهیم). اما وقتی `TransformersObjectDetectionProvider` نوشته شد، مشخص شد که این فیلد را _اعلام_ کرده (در `ObjectDetectionArtifact`) اما هیچ‌وقت واقعاً پر نمی‌کرد — همیشه یک رشته‌ی خالی `""` می‌ماند، بدون این‌که هیچ تستی این را بگیرد. `CaptionArtifact` هم اصلاً این فیلد را نداشت. هر دو در همان زمان اصلاح شدند تا با الگوی مشترک هماهنگ باشند. درسش: **داشتن یک فیلد در تعریف کلاس، تضمین نمی‌کند که کد واقعاً آن را پر می‌کند** — این دقیقاً همان چیزی است که تست‌های یکپارچگی (integration test) با داده‌ی واقعی برای گرفتنش لازم‌اند، نه فقط تست واحد با داده‌ی ساختگی.

## نگاه دقیق به یک Provider واقعی: `FFmpegFrameExtractionProvider`

بیایید این یکی را کامل بخوانیم، چون ساده‌ترین الگو (فراخوانی یک برنامه‌ی خط‌فرمان) را نشان می‌دهد.

```python
def run(self, media: Media) -> list[Artifact[Any]]:
    if not isinstance(media, VideoMedia):
        raise TypeError(f"Expected VideoMedia, got {type(media).__name__}")

    source = media.metadata.get("source")
    if not source:
        raise ProviderError("VideoMedia has no 'source' path in metadata ...")

    if shutil.which(self._ffmpeg_binary) is None:
        raise FFmpegBinaryMissingError(self._ffmpeg_binary)

    duration = media.duration if media.duration > 0 else 1.0
    timestamps = self._evenly_spaced_timestamps(duration, self._frame_count)

    artifacts = []
    for index, timestamp in enumerate(timestamps):
        frame_path = output_dir / f"{media.id}_frame_{index:04d}.png"
        self._extract_frame(source, timestamp, frame_path)
        artifacts.append(
            FrameExtractionArtifact(
                media_id=media.id,
                provider=self.name,
                frame_path=str(frame_path),
                timestamp_seconds=timestamp,
                frame_index=index,
            )
        )
    return artifacts
```

قدم‌به‌قدم چه اتفاقی می‌افتد:

1. **بررسی نوع** — اگر `media` از نوع `VideoMedia` نباشد، بلافاصله خطا می‌دهد. (نه این‌که سه خط بعد یک خطای گنگ بگیریم.)
2. **بررسی وجود مسیر فایل** — `media.metadata["source"]` باید مسیر فایل واقعی را داشته باشد (این را `LocalVideoLoader` هنگام بارگذاری می‌گذارد).
3. **بررسی نصب‌بودن ffmpeg** — با `shutil.which`، قبل از تلاش برای اجرا چک می‌کند که برنامه اصلاً روی سیستم نصب است.
4. **محاسبه‌ی زمان‌بندی قاب‌ها** — اگر بخواهیم ۸ قاب از یک ویدیوی ۱۰ ثانیه‌ای بگیریم، این تابع محاسبه می‌کند که هر قاب باید در چه ثانیه‌ای باشد (به‌طور مساوی پخش‌شده).
5. **اجرای واقعی و ساخت Artifact** — برای هر قاب، دستور `ffmpeg` واقعی اجرا می‌شود و یک `FrameExtractionArtifact` ساخته می‌شود.

## چرا هر Provider «خطاهای خودش را می‌بلعد و دوباره پرتاب می‌کند»؟

```python
try:
    subprocess.run(command, capture_output=True, check=True, timeout=30)
except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
    raise ProviderError(
        f"ffmpeg frame extraction failed at t={timestamp}: {exc}"
    ) from exc
```

اگر این کار را نکنیم، کسی که از `Pipeline` استفاده می‌کند باید بداند که باید مثلاً `subprocess.CalledProcessError` را هم بگیرد — یعنی باید جزئیات پیاده‌سازی داخلی هر Provider را بداند. با تبدیل هر خطا به `ProviderError`، کافی است فقط یک نوع خطا را بشناسی، مهم نیست پشت‌صحنه از `ffmpeg` استفاده شده یا از یک کتابخانه‌ی پایتونی.

## نکته‌ی مشترک بین همه: `source_frame_path`

پنج‌تا از این هفت Provider (تشخیص چهره، تشخیص متن، توضیح تصویر، تشخیص شیء، و به‌طور غیرمستقیم استخراج قاب) از یک الگوی مشترک استفاده می‌کنند: وقتی روی یک قاب استخراج‌شده اجرا می‌شوند، مسیر فایل آن قاب را در خروجی خودشان نگه می‌دارند (`source_frame_path`). این الگو، پایه‌ی «ترکیب چند حوزه» (cross-domain) در لایه‌ی دانش است که در فایل بعد توضیح می‌دهیم — و همان‌طور که در بخش بالا دیدی، این الگو آن‌قدر مهم است که نبودِ سرِ‌جایش، یک باگ واقعی محسوب شد.

---

مرحله‌ی بعد: [`07-knowledge-layer.md`](07-knowledge-layer.md) — چطور از این Artifact های خام، دانش واقعی ساخته می‌شود.
