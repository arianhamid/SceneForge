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
print(media.codec)  # "unknown"
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
class Artifact[T](ABC):
    id: UUID = field(default_factory=uuid4)
    kind: ArtifactKind = ArtifactKind.ARTIFACT
    category: ArtifactCategory = ArtifactCategory.METADATA
    provider: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: T = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
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

نکته‌ی خیلی مهم: **`parents`** یک تاپل (tuple) از شناسه‌های Artifact های دیگر است. این فیلد رد پای «این از کجا آمد» را نگه می‌دارد. خودِ مقدار `Artifact` درجا تغییر نمی‌کند؛ اصلاح باید یک Artifact جدید بسازد که در `parents` به قبلی اشاره کند. اما `ArtifactStore` فعلی یک cache قابل‌حذف است، پس ماندگاری همیشگیِ شاهد فقط از frozen بودن dataclass نتیجه نمی‌شود — همین تفاوت یکی از انگیزه‌های `KnowledgeRecordStore` در ADR-0024 بود.

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
print(result.artifacts)  # لیست Artifact های ساخته‌شده
print(result.from_cache)  # آیا از کش خوانده شد؟
print(result.duration_seconds)  # چقدر طول کشید؟
```

### چرا این‌قدر پارامتر دارد؟

هرکدام از این پارامترها، جواب یک نیاز واقعی است که در طول توسعه پیدا شد:

- `enricher` — چون `Media` اول اطلاعات اشتباه دارد (بالا توضیح داده شد).
- `store` — چون بدون آن، هربار که یک ویدیو را دوباره پردازش کنی، Provider دوباره (و دوباره، و دوباره) اجرا می‌شود — حتی اگر چیزی تغییر نکرده باشد.
- `max_retries` — چون بعضی Providerها (مثلاً آن‌هایی که با یک مدل کار می‌کنند) گاهی به‌طور موقت شکست می‌خورند.

### کلید کش چطور ساخته می‌شود؟ (و باگ واقعی‌ای که در آن پیدا شد)

نسخه‌ی اول این تابع این‌طور بود:

```python
def content_key(media, provider_name, provider_version):
    basis = f"{media.name}:{media.id}:{provider_name}:{provider_version}"
    return sha256(basis.encode()).hexdigest()
```

این نسخه یک باگ واقعی داشت که مدت‌ها کشف نشده بود: `media.id` — همان‌طور که در فایل ۳ دیدی — هر بار که یک فایل بارگذاری می‌شود، یک `UUID` **تصادفیِ جدید** می‌گیرد. یعنی اگر همان ویدیو را دو بار بارگذاری می‌کردی (حتی بدون هیچ تغییری در فایل)، دو `media.id` متفاوت می‌گرفتی → دو کلید کش متفاوت → کش هرگز واقعاً «hit» نمی‌شد. مشکل دوم، حتی بدتر: اگر دو Provider با یک نام و نسخه، اما تنظیمات داخلی متفاوت (مثلاً دو مدل Whisper با پارامتر متفاوت) روی همان یک شیء `Media` اجرا می‌شدند، هر دو **همان کلید** را می‌ساختند — یعنی نتیجه‌ی اشتباه از کش برگردانده می‌شد، بدون هیچ خطایی.

یک بررسیِ پیاده‌سازی (implementation review) این باگ را با کد واقعی بازتولید کرد، نه با حدس. راه‌حل (`ADR-0024`) نسخه‌ی فعلی تابع است:

```python
def content_key(media, provider_name, provider_version, execution_fingerprint=""):
    basis = (
        f"{media_content_identity(media)}:{provider_name}:{provider_version}"
        f":{execution_fingerprint}"
    )
    return sha256(basis.encode("utf-8")).hexdigest()
```

دو تغییر کلیدی:

1. **`media_content_identity(media)` به‌جای `media.id`.** اگر `Media` به یک فایل واقعی روی دیسک اشاره کند، این تابع بایت‌های واقعی فایل را هش می‌کند — یعنی بارگذاری دوباره‌ی همان فایل، همیشه همان هویت را می‌دهد، هرچند `media.id` هر بار عوض شود. اگر `Media` هیچ فایل پشتیبانی نداشته باشد (مثلاً در تست‌ها، رسانه‌ی مصنوعی)، به‌جایش از هش نامِ `media.name` استفاده می‌کند — یک راه‌حل ضعیف‌تر اما مستند و صادقانه، نه پنهان‌شده.
2. **`execution_fingerprint` جدید.** هر Provider می‌تواند این را override کند تا تنظیمات داخلی‌اش (نه فقط نام و نسخه) هم در کلید کش دخیل باشد. مثلاً `WhisperTranscribeProvider` این را از پارامترهای `transcribe_kwargs` خودش می‌سازد — دقیقاً همان سناریویی که باگ دوم را ایجاد می‌کرد.

درسی که از این باگ می‌شود گرفت: **یک شناسه‌ی «هرباره تصادفی» هرگز نباید پایه‌ی یک کلید کش باشد که قرار است بین دو اجرای مختلف پایدار بماند.** اگر می‌خواهی یک هویت پایدار بسازی، باید از چیزی استفاده کنی که واقعاً از _محتوا_ می‌آید، نه از یک شمارنده یا `uuid4()` که هر بار عوض می‌شود.

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
