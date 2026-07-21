# ۴. مفاهیم پایه‌ی پروژه

این فایل مهم‌ترین کلاس‌های پروژه را یکی‌یکی توضیح می‌دهد — با کد واقعی، نه خلاصه‌شده.

## Media — نماینده‌ی یک فایل ورودی

مسیر فایل: `sceneforge/media/base.py`

```python
@dataclass(frozen=True, slots=True)
class Media:
    name: str
    id: UUID = field(default_factory=uuid4)
    metadata: dict[str, Any] = field(default_factory=dict)
```

سه زیرکلاس دارد: `ImageMedia`، `VideoMedia`، `AudioMedia` — هرکدام فیلدهای اختصاصی خودشان را اضافه می‌کنند (مثلاً `VideoMedia` فیلد `fps` و `duration` دارد).

### چرا اطلاعاتش اول اشتباه است؟

وقتی یک ویدیو را بارگذاری می‌کنی:

```python
from sceneforge.media.video_loader import LocalVideoLoader
media = LocalVideoLoader("movie.mp4").load()
print(media.duration)  # 0.0  ← این درست نیست!
print(media.codec)     # "unknown"
```

`LocalVideoLoader` عمداً سبک است — فقط به سیستم فایل نگاه می‌کند، فایل را رمزگشایی نمی‌کند. برای گرفتن مقدار واقعی، باید از یک **Enricher** استفاده کنی:

```python
from sceneforge.contrib.ffmpeg import FFprobeEnricher
enriched = FFprobeEnricher().enrich(media)
print(enriched.duration)  # 120.5  ← حالا درست است
```

نکته: `enriched` یک شیء **جدید** است. `media` اصلی دست‌نخورده باقی می‌ماند (چون `Media` غیرقابل‌تغییر است — به فایل ۳ نگاه کن).

## Capability — قابلیت

مسیر فایل: `sceneforge/core/capability.py`

```python
class Capability(StrEnum):
    CAPTION = "caption"
    TRANSCRIBE = "transcribe"
    DETECT_SCENES = "detect_scenes"
    FRAME_EXTRACTION = "frame_extraction"
    FACE_DETECTION = "face_detection"
    OCR = "ocr"
    # ...
```

`Capability` یک **اسم برای یک نوع کار** است، نه یک مدل خاص. کد هرگز نمی‌نویسد «از Whisper استفاده کن»؛ می‌نویسد «به قابلیت `TRANSCRIBE` نیاز دارم».

## Artifact — یک مشاهده‌ی خام

مسیر فایل: `sceneforge/core/artifact.py`

```python
@dataclass(frozen=True, slots=True)
class Artifact(ABC, Generic[T]):
    id: UUID = field(default_factory=uuid4)
    kind: ArtifactKind = ArtifactKind.ARTIFACT
    category: ArtifactCategory = ArtifactCategory.METADATA
    provider: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: T = None
    metadata: dict[str, Any] = field(default_factory=dict)
    parents: tuple[UUID, ...] = ()
```

هر Provider واقعی، زیرکلاس اختصاصی خودش را از `Artifact` می‌سازد. مثلاً:

```python
@dataclass(frozen=True, slots=True)
class FrameExtractionArtifact(Artifact[None]):
    media_id: UUID = field(default_factory=uuid4)
    frame_path: str = ""
    timestamp_seconds: float = 0.0
```

نکته‌ی خیلی مهم: **`parents`** یک تاپل (tuple) از شناسه‌های Artifact های دیگر است. این فیلد رد پای «این از کجا آمد» را نگه می‌دارد. هیچ Artifact‌ای هرگز حذف نمی‌شود؛ اگر باید اصلاح شود، یک Artifact جدید ساخته می‌شود که در `parents` خودش به Artifact قدیمی اشاره می‌کند.

## Provider — تولیدکننده‌ی Artifact

مسیر فایل: `sceneforge/core/provider.py` (نسخه‌ی وراثتی) و `sceneforge/core/provider_protocol.py` (نسخه‌ی Protocol)

هر Provider باید این چهار چیز را داشته باشد:

```python
class OpenCVFaceDetectionProvider(Provider):
    @property
    def name(self) -> str:
        return "opencv_face_detection"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.FACE_DETECTION})

    def run(self, media: Media) -> list[Artifact[Any]]:
        # ... منطق واقعی اینجاست
        return artifacts
```

### چرا `version` این‌قدر مهم است؟

`version` فقط برای مستندسازی نیست — بخشی از **کلید کش** است (توضیح کامل در بخش بعد). اگر منطق داخلیِ یک Provider تغییر کند (مثلاً یک مدل جدیدتر)، باید `version` را عوض کنی؛ وگرنه سیستم فکر می‌کند نتیجه‌ی قبلی هنوز معتبر است و آن را دوباره تحویل می‌دهد، حتی اگر دیگر درست نباشد.

## Pipeline — هماهنگ‌کننده‌ی اجرا

مسیر فایل: `sceneforge/core/pipeline.py`

`Pipeline` مسئول این مراحل است: **غنی‌سازی (enrich) → بررسی سازگاری → بررسی کش → اجرای Provider → ذخیره در کش**.

```python
from sceneforge.core.pipeline import Pipeline
from sceneforge.contrib.opencv import OpenCVFaceDetectionProvider, OpenCVImageEnricher
from sceneforge.core.storage import FileArtifactStore

pipeline = Pipeline(
    provider=OpenCVFaceDetectionProvider(),
    enricher=OpenCVImageEnricher(),
    store=FileArtifactStore("./cache"),
    max_retries=2,
)

result = pipeline.run_detailed(media)
print(result.artifacts)         # لیست Artifact های ساخته‌شده
print(result.from_cache)        # آیا از کش خوانده شد؟
print(result.duration_seconds)  # چقدر طول کشید؟
```

### چرا این‌قدر پارامتر دارد؟

هرکدام از این پارامترها، جواب یک نیاز واقعی است که در طول توسعه پیدا شد:

- `enricher` — چون `Media` اول اطلاعات اشتباه دارد (بالا توضیح داده شد).
- `store` — چون بدون آن، هربار که یک ویدیو را دوباره پردازش کنی، Provider دوباره (و دوباره، و دوباره) اجرا می‌شود — حتی اگر چیزی تغییر نکرده باشد.
- `max_retries` — چون بعضی Providerها (مثلاً آن‌هایی که با یک مدل کار می‌کنند) گاهی به‌طور موقت شکست می‌خورند.

### کلید کش چطور ساخته می‌شود؟

```python
def content_key(media, provider_name, provider_version):
    basis = f"{media.name}:{media.id}:{provider_name}:{provider_version}"
    return sha256(basis.encode()).hexdigest()
```

یعنی: اگر همان `media`، همان Provider، و همان نسخه باشد → همان کلید → از کش خوانده می‌شود. اگر نسخه‌ی Provider عوض شود → کلید جدید → دوباره اجرا می‌شود. این دقیقاً چیزی است که باعث می‌شود شعار «یک فیلم فقط یک‌بار تحلیل می‌شود» واقعی باشد، نه فقط یک حرف قشنگ.

## CapabilityRegistry — کدام Media با کدام Capability سازگار است؟

مسیر فایل: `sceneforge/core/capability_registry.py`

```python
registry = CapabilityRegistry()
registry.register(Capability.FACE_DETECTION, {ImageMedia, VideoMedia})
```

قبل از این‌که `Pipeline` یک Provider را اجرا کند، چک می‌کند که آیا نوع `Media` ورودی با قابلیت‌های آن Provider سازگار است یا نه. مثلاً اگر بخواهی `OpenCVFaceDetectionProvider` را روی یک فایل صوتی اجرا کنی، قبل از اجرا خطا می‌گیری — نه وسط اجرا با یک خطای گنگ.

نکته‌ی فنی: این کلاس **قابل‌تزریق (injectable)** است — یعنی هر `Pipeline` می‌تواند رجیستری خودش را داشته باشد. قبلاً این اطلاعات در یک متغیر سراسری (global) ذخیره می‌شد که یک باگ واقعی بود: دو `Pipeline` مختلف می‌توانستند روی هم اثر بگذارند بدون این‌که هیچ‌کدام از وجود دیگری خبر داشته باشند. این مشکل در [`docs/adr/0007-injectable-capability-registry.md`](../adr/0007-injectable-capability-registry.md) حل شد.

---

مرحله‌ی بعد: [`05-data-flow.md`](05-data-flow.md) — حالا که این مفاهیم را می‌شناسی، ببینیم وقتی یک اسکریپت واقعی اجرا می‌شود، دقیقاً چه اتفاقی می‌افتد.
