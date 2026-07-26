# راهنمای جامع پروژه SceneForge

> **چارچوب باز برای هوشمندی روایی (Narrative Intelligence)**

> **فیلم‌ها فقط ویدیو نیستند. آن‌ها دنیاهایی هستند که منتظر درک شدن‌اند.**

---

## فهرست مطالب

1. [معرفی کلی پروژه](#۱-معرفی-کلی-پروژه)
2. [چرا SceneForge؟](#۲-چرا-sceneforge)
3. [چشم‌انداز و فلسفه](#۳-چشم‌انداز-و-فلسفه)
4. [اهداف و ضد-اهداف](#۴-اهداف-و-ضد-اهداف)
5. [مدل دامنه (Domain Model)](#۵-مدل-دامنه)
6. [معماری لایه‌ای](#۶-معماری-لایه‌ای)
7. [مشخصات فنی (Specifications)](#۷-مشخصات-فنی)
8. [سازندگان دانش (Knowledge Builders)](#۸-سازندگان-دانش)
9. [ساختار کد منبع](#۹-ساختار-کد-منبع)
10. [راهنمای پیاده‌سازی](#۱۰-راهنمای-پیاده‌سازی)
11. [تست‌ها و کیفیت کد](#۱۱-تست‌ها-و-کیفیت-کد)
12. [ثبت تصمیمات معماری (ADR)](#۱۲-ثبت-تصمیمات-معماری)
13. [مشارکت در پروژه](#۱۳-مشارکت-در-پروژه)
14. [وضعیت فعلی پروژه](#۱۴-وضعیت-فعلی-پروژه)
15. [واژه‌نامه فنی](#۱۵-واژه‌نامه-فنی)

---

## ۱. معرفی کلی پروژه

### ۱.۱. SceneForge چیست؟

SceneForge یک چارچوب متن‌باز (Open Source) برای استخراج، سازمان‌دهی، استدلال و بازیابی دانش از فیلم‌ها و ویدیوها است. برخلاف خطوط لوله (Pipeline) هوش مصنوعی سنتی که پس از تولید کپشن یا JSON متوقف می‌شوند، SceneForge یک درک ساختاریافته از داستان‌های بصری می‌سازد که می‌تواند بسیاری از برنامه‌های کاربردی مختلف را پشتیبانی کند.

### ۱.۲. ایده اصلی

یک فیلم فقط یک‌بار تحلیل می‌شود. درک آن برای همیشه قابل استفاده مجدد است.

### ۱.۳. زبان و فناوری

- **زبان برنامه‌نویسی:** Python 3.11+
- **سیستم ساخت:** Hatchling
- **وضعیت توسعه:** Pre-Alpha (مرحله پیش-آلفا)
- **مجوز:** Apache-2.0
- **تعداد تست‌ها:** ۳۱۵+ تست در حال اجرای موفق
- **فایل‌های منبع:** ۷۹ فایل منبع با mypy --strict خالص

### ۱.۴. کاربردهای نمونه

- تولید کمیک از فیلم
- تولید استوری‌بورد
- تولید رمان
- جستجوی فیلم
- ردیابی شخصیت‌ها
- درک صحنه
- تولید مجموعه داده (Dataset)
- لوله‌های RAG
- ابزارهای آموزشی
- تحلیل ویدیو

---

## ۲. چرا SceneForge؟

### ۲.۱. مشکل فعلی

خطوط لوله هوش مصنوعی ویدیو امروزی به شدت به مدل‌های خاصی وابسته هستند:

```
فیلم → مدل → برنامه کاربردی
```

تغییر مدل معمولاً نیازمند بازنویسی برنامه کاربردی است.

### ۲.۲. راه‌حل SceneForge

SceneForge یک معماری جدید معرفی می‌کند:

```
فیلم → مشاهدات (Artifacts) → دانش (Knowledge) → هوشمندی (Intelligence) → برنامه‌های کاربردی
```

برنامه‌های کاربردی هرگز به مدل‌های هوش مصنوعی وابسته نیستند. آن‌ها به دانش وابسته‌اند.

### ۲.۳. مزایای کلیدی

| ویژگی | توضیح |
|--------|--------|
| **独立 از مدل** | تعویض مدل پشت هر قابلیت نیازمند تغییر فراخواننده نیست |
| **ذخیره‌سازی محتوای آدرس‌پذیر** | "یک‌بار تحلیل، برای همیشه بازیابی" به صورت تحت‌اللفظی |
| **معماری افزونه‌پذیر** | قابلیت‌ها از طریق افزونه‌ها (Plugin) کشف و بارگذاری می‌شوند |
| **بدون حالت پنهان** | دو Pipeline در یک فرآیند نمی‌توانند بدون اطلاع یکدیگر تأثیر بگذارند |
| **ابزار اول** | مستندات به عنوان یک ویژگی درجه یک در نظر گرفته می‌شوند |
| **محلی-اول** | بدون وابستگی اجباری ابری برای حلقه اصلی |

---

## ۳. چشم‌انداز و فلسفه

### ۳.۱. ستاره شمالی (North Star)

**یک فیلم فقط یک‌بار تحلیل می‌شود. درک آن به یک دارایی دائمی، قابل استعلام، قابل افزایش و ماندگارتر از هر مدل یا برنامه کاربردی تبدیل می‌شود.**

به صورت مشخص:
- **درک:** تبدیل فریم‌های خام، صدا و زمان به دانش ساختاریافته — صحنه‌ها، شخصیت‌ها، مکان‌ها، گفتگو، حس و حال
- **سازمان‌دهی:** دانش در یک مکان زندگی می‌کند (گراف دانش)، نه پراکنده در حافظه‌های نهان برنامه‌های مختلف
- **استدلال:** برنامه‌های کاربردی از گراف دانش استعلام می‌کنند، آن را دوباره استخراج نمی‌کنند
- **بازیابی:** کپشنی که یک‌بار برای یک مکان تولید شده، توسط هر صحنه در آن مکان بازیابی می‌شود
- **افزایش:** مدل جدید، برنامه جدید، نوع رسانه جدید — همه بدون تغییر کار موجود اضافه می‌شوند

### ۳.۲. اصول طراحی

1. **معماری قبل از پیاده‌سازی** — مرزهای لایه محصول هستند
2. **دانش قبل از تولید** — SceneForge درک تولید می‌کند
3. **قابلیت‌ها قبل از مدل‌ها** — کد به `Capability.CAPTION` وابسته است، هرگز به "GPT-4V"
4. **مشاهدات تغییرناپذیر، اصلاحات صریح** — چیزی که قبلاً مشاهده شده هرگز تغییر نمی‌کند
5. **افزونه‌ها به جای کوپلینگ سخت** — هر پیاده‌سازی قابلیت یک افزونه است
6. **بدون حالت پنهان** — اگر دو Pipeline در یک فرآیند بتوانند بر هم تأثیر بگذارند، آن باگ است
7. **اثبات قبل از رسمی‌سازی** — یک برش کاربردی واقعی بهتر از یک لایه زیبای مشخص‌شده است
8. **محلی-اول، بی‌طرف تأمین‌کننده** — بدون وابستگی ابری اجباری
9. **فکر کردن به سال‌ها، نه اسپرینت‌ها** — اما بهانه‌ای برای نوشتن اسناد حکومتی قبل از وجود دومین Provider واقعی نیست

### ۳.۳. تعریف موفقیت

موفقیت این نیست که "SceneForge هشت لایه به طور کامل پیاده‌سازی شده." موفقیت این است: **کسی یک فیلم واقعی را یک‌بار از SceneForge عبور دهد، سپس سه چیز مختلف — یک کمیک، یک متن قابل جستجو، یک گالری مکان — از آن تحلیل واحد بسازد، بدون اجرای مجدد هیچ مدلی.**

---

## ۴. اهداف و ضد-اهداف

### ۴.۱. اهداف

- درک فیلم‌ها به جای توصیف صرف فریم‌ها
- ساختن دانش ساختاریافته قابل بازیابی
- مستقل از مدل ماندن
- پشتیبانی از ارائه‌دهندگان محلی و ابری AI
- تشویق تحقیق تکرارپذیر
- به عنوان پایه‌ای برای برنامه‌های کاربردی متعدد

### ۴.۲. ضد-اهداف (SceneForge اینها نیست)

- **یک بسته‌بند LLM** — ارائه‌دهندگان قابل تعویض هستند، درک دائمی است
- **یک تولیدکننده کمیک** — تولید کمیک فقط یک برنامه کاربردی است
- **مجموعه‌ای از اسکریپت‌ها** — هر قابلیت باید در یک معماری منسجم ادغام شود
- **یک معیار مدل** — SceneForge درک را اندازه می‌گیرد، نه محبوبیت مدل را
- **یک گردش کار وابسته به یک فروشنده** — هر فروشنده ابری می‌تواند فردا ناپدید شود
- **یک مونولیت** — همه چیز باید از طریق افزونه‌ها قابل تعویض باشد

---

## ۵. مدل دامنه

### ۵.۱. فیلم (Movie)

یک منبع اطلاعات روایی. فقط حاوی رسانه است.

### ۵.۲. مشاهده (Artifact)

یک مشاهده تغییرناپذیر که مستقیماً از رسانه استخراج شده است.

**ویژگی‌ها:**
- تغییرناپذیر (Immutable)
- زمان‌محور (Timestamped)
- قابل سریال‌سازی (Serializable)
- قابل ردیابی (Traceable)
- تکرارپذیر (Reproducible)

**مثال‌ها:** فریم، رونوشت، OCR، کپشن، بردار جاسازی (Embedding)

**ممنوعیات:** مشاهدات هرگز نباید حاوی استدلال، هویت شخصیت، خلاصه داستان، روابط، موضوعات یا پیش‌بینی باشند.

### ۵.۳. نهاد (Entity)

یک مفهوم قابل بازیابی که از مشاهدات مشتق شده است.

**مثال‌ها:** شخصیت، مکان، شیء، صحنه، فصل، رویداد، گفتگو

**ویژگی‌ها:**
- تغییرناپذیر
- `parents` شناسه‌های مشاهدات ورودی را ثبت می‌کند
- `metadata` حاوی اطلاعات اضافی سازنده است
- `Provenance` اطلاعات منشأ را تایپ می‌کند (سازنده، شناسه‌های مشاهدات منبع، اطمینان)

### ۵.۴. رابطه (Relationship)

یک اتصال بین نهادها. به صورت یک `Entity` با نوع `EntityKind.RELATIONSHIP` نمایش داده می‌شود که `parents` به شناسه‌های دو نهاد مرتبط اشاره می‌کند.

**مثال‌های واقعی:** صحنه N قبل از صحنه N+1 (`SceneSequenceBuilder`)

**مثال‌های فرضی:** شخصیت در صحنه حضور دارد، گفتگو متعلق به شخصیت است، صحنه در مکان رخ می‌دهد

### ۵.۵. گراف دانش (Knowledge Graph)

مجموعه کامل نهادها و روابط. به عنوان درک مرکزی یک فیلم عمل می‌کند.

### ۵.۶. هوشمندی (Intelligence)

اطلاعات استنتاج‌شده از دانش. مثال‌ها: رشد شخصیت، موضوع، تعارض، کنایه، سرعت روایی، نمادگرایی

### ۵.۷. قابلیت (Capability)

یک ویژگی چارچوب. مثال‌ها: کپشن تصویر، رونویسی صدا، تشخیص صحنه، ردیابی شخصیت‌ها. هر ارائه‌دهنده قابلیت‌ها را پیاده‌سازی می‌کند.

### ۵.۸. ارائه‌دهنده (Provider)

پیاده‌سازی یک یا چند قابلیت. ارائه‌دهندگان قابل تعویض هستند.

### ۵.۹. خط لوله (Pipeline)

هماهنگ‌کننده اجرای یک ارائه‌دهنده روی یک شیء رسانه: اعتبارسنجی سازگاری، غنی‌سازی اختیاری، بررسی حافظه نهان، اجرای ارائه‌دهنده، ذخیره در حافظه نهان.

### ۵.۱۰. افزونه (Plugin)

بسته‌ای قابل نصب که SceneForge را گسترش می‌دهد. افزونه‌ها می‌توانند قابلیت‌ها، ارائه‌دهندگان، استدلال‌گرها، برنامه‌های کاربردی و سازندگان دانش ارائه دهند.

---

## ۶. معماری لایه‌ای

### ۶.۱. نمای کلی

```
                    برنامه‌های کاربردی (Applications)
                              │
                    موتور هوشمندی (Intelligence Engine)
                              │
                    گراف دانش (Knowledge Graph)
                              │
                    سازندگان دانش (Knowledge Builders)
                              │
                    مشاهدات (Artifacts) ◄── ArtifactStore
                              │
                    ارائه‌دهندگان (Providers)
                              │
                    زیرساخت اجرا (Runtime Infrastructure)
                              │
                    رسانه مبدأ (Source Media)
```

### ۶.۲. لایه ۰ — رسانه (Media)

ورودی‌های خارجی. فیلم‌ها، برنامه‌های تلویزیونی، ویدیوهای YouTube، دنباله تصاویر، صدا، پخش زنده.

**Rule:** SceneForge هرگز رسانه را تغییر نمی‌دهد.

**انواع رسانه:**

```python
@dataclass(frozen=True, slots=True)
class Media:
    name: str
    id: UUID
    metadata: dict[str, Any]

@dataclass(frozen=True, slots=True, kw_only=True)
class ImageMedia(Media):
    width: int
    height: int
    fmt: str
    # ویژگی‌ها: aspect_ratio, pixel_count

@dataclass(frozen=True, slots=True, kw_only=True)
class VideoMedia(Media):
    duration: float
    codec: str
    fps: float
    # ویژگی: frame_count

@dataclass(frozen=True, slots=True, kw_only=True)
class AudioMedia(Media):
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int = 16
```

**بارگذاران محلی:**
- `LocalImageLoader(path)` → `ImageMedia`
- `LocalVideoLoader(path)` → `VideoMedia`
- `LocalAudioLoader(path)` → `AudioMedia`

**اصلاح متاداتای جایگزین: `Media.evolve()`**

رسانه تغییرناپذیر است، بنابراین هیچ چیزی در جا تغییر نمی‌کند. `evolve()` نمونه جدیدی از همان نوع با فیلدهای جایگزین شده برمی‌گرداند:

```python
video = VideoMedia(name="movie.mp4", duration=0.0, codec="unknown", fps=0.0)
enriched = video.evolve(duration=120.0, codec="h264", fps=24.0)
# enriched is not video  → True (نمونه جدید)
# enriched.id == video.id → True (همان منطقی رسانه، واقعیت‌های اصلاح شده)
# video.duration          → 0.0 (اصلی دست‌نخورده)
```

### ۶.۳. لایه ۱ — زیرساخت اجرا (Runtime Infrastructure)

زیرساخت اجرا خدمات زمان اجرا را برای پردازش رسانه فراهم می‌کند.

**اجزاء:**
- `ProcessingContext` — وضعیت اجرایی را ذخیره می‌کند، پیشرفت را گزارش می‌دهد، لغو را پشتیبانی می‌کند
- پروتکل `Decoder` — تعریف می‌کند چگونه رسانه به بازنمایی‌ها رمزگشایی می‌شود

**پروتکل Decoder:**

```python
class Decoder(Protocol):
    def decode(self, media: Media) -> Any: ...
```

ارائه‌دهندگان درخواست رمزگشایی از طریق پروتکل Decoder می‌کنند، هرگز آن را مستقیماً انجام نمی‌دهند.

**انواع بازنمایی:**
- `ImageRepresentation` — پیکسل‌های تصویر رمزگشایی شده با متاداتا
- `VideoRepresentation` — متاداتای ویدیو با دسترسی به فریم‌ها
- `AudioRepresentation` — متاداتای صدا با دسترسی به قطعات

### ۶.۴. لایه ۲ — ارائه‌دهندگان (Providers)

ارائه‌دهندگان با سیستم‌های خارجی ارتباط برقرار می‌کنند.

**پروتکل Provider:**

```python
class Provider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def capabilities(self) -> frozenset[Capability]: ...

    def run(self, media: Media) -> list[Artifact]: ...
```

**ویژگی‌های کلیدی:**
- مبتنی بر پروتکل (نوع‌دهی ساختاری) و مبتنی بر ABC (نوع‌دهی اسمی)
- پس از ساخت تغییرناپذیر
- خالص: بدون جهش، بدون حالت، بدون اثرات جانبی
- فقط کتابخانه استاندارد در `sceneforge.core`

**ارائه‌دهندگان هماهنگ و ناهمگام:**

```python
# ارائه‌دهنده هماهنگ (Sync)
class MySyncProvider(Provider):
    def run(self, media: Media) -> list[Artifact]:
        # پردازش هماهنگ
        ...

# ارائه‌دهنده ناهمگام (Async)
class MyAsyncProvider(AsyncProvider):
    async def run(self, media: Media) -> list[Artifact]:
        # پردازش ناهمگام
        ...

# تبدیل هماهنگ به ناهمگام
async_provider = SyncProviderAdapter(MySyncProvider())
pipeline = AsyncPipeline(async_provider, max_concurrency=3, timeout_seconds=120)
batch = await pipeline.run_many(scene_clips)
```

**ارائه‌دهندگان واقعی موجود:**

| ارائه‌دهنده | قابلیت | نوع | وابستگی |
|-------------|---------|------|----------|
| `FFmpegFrameExtractionProvider` | `FRAME_EXTRACTION` | Subprocess | ffmpeg/ffprobe |
| `PySceneDetectProvider` | `DETECT_SCENES` | الگوریتمی | scenedetect |
| `WhisperTranscribeProvider` | `TRANSCRIBE` | مدلی | faster-whisper |
| `OpenCVFaceDetectionProvider` | `FACE_DETECTION` | الگوریتمی | opencv-python |
| `MediaHashProvider` | `METADATA` | الگوریتمی | hashlib |

### ۶.۵. لایه ۳ — مشاهدات (Artifacts)

مشاهدات تغییرناپذیر هستند. هیچ استدلالی ندارند.

**ساختار پایه:**

```python
@dataclass(frozen=True, slots=True)
class Artifact(ABC, Generic[T]):
    id: UUID                              # شناسه خودکار
    kind: ArtifactKind                    # نوع مشاهده
    category: ArtifactCategory            # دسته‌بندی
    provider: str                         # نام ارائه‌دهنده
    created_at: datetime                  # زمان ایجاد UTC
    payload: T                            # داده مشاهده
    metadata: Mapping[str, Any]           # متاداتای ارائه‌دهنده
    parents: tuple[UUID, ...]             # شناسه‌های مشاهدات والد
```

**انواع مشاهده (ArtifactKind):**
`ARTIFACT`, `FRAME`, `TRANSCRIPT`, `SCENE_CUT`, `CAPTION`, `OCR`, `EMBEDDING`, `FACE_DETECTION`, `OBJECT_DETECTION`, `AUDIO_SEGMENT`

**دسته‌بندی مشاهدات (ArtifactCategory):**
`METADATA`, `ANALYSIS`, `DETECTION`, `RECOGNITION`, `DERIVED`, `TRANSFORMATION`

### ۶.۶. پایداری (Persistence) — مقطعی، نه لایه شماره‌دار

`ArtifactStore` یک کانال فرعی است که هر لایه از مشاهدات به بالا می‌تواند از آن بخواند و در آن بنویسد.

**مسئولیت‌ها:**
- حافظه نان خروجی ارائه‌دهنده، کلیدگذاری‌شده بر اساس هویت رسانه + نام ارائه‌دهنده + نسخه
- "قبلاً تحلیل شده" را به یک واقعیت قابل استعلام تبدیل می‌کند

**پیاده‌سازی‌ها:**
- `FileArtifactStore` — ذخیره‌سازی فایلی
- `InMemoryArtifactStore` — حافظه درون‌فرآیندی

### ۶.۷. لایه ۴ — سازندگان دانش (Knowledge Builders)

سازندگان دانش مشاهدات را به نهادهای قابل بازیابی ادغام می‌کنند.

**پروتکل KnowledgeBuilder:**

```python
class KnowledgeBuilder(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def build(self, artifacts: list[Artifact[Any]]) -> list[Entity[Any]]: ...
```

**دو شکل سازنده:**

```
مشاهدات → KnowledgeBuilder.build()      → نهادها   (سازندگان نهاد)
نهادها   → RelationshipBuilder.relate()  → نهادها   (سازندگان رابطه)
```

### ۶.۸. لایه ۵ — گراف دانش (Knowledge Graph)

پایگاه داده مرکزی درک. شامل شخصیت‌ها، مکان‌ها، اشیاء، رویدادها، صحنه‌ها، گفتگوها، روابط و خط زمانی.

### ۶.۹. لایه ۶ — هوشمندی (Intelligence)

استدلال‌گرها منحصراً روی گراف دانش عمل می‌کنند. مثال‌ها: قوس داستانی، قوس شخصیت، تشخیص موضوع، جریان احساسات، تحلیل تعارض.

### ۶.۱۰. لایه ۷ — برنامه‌های کاربردی (Applications)

برنامه‌های کاربردی هوشمندی را مصرف می‌کنند. هرگز مستقیماً استخراج انجام نمی‌دهند.

### ۶.۱۱. قوانین وابستگی

**مجاز:**
```
رسانه → زیرساخت اجرا → ارائه‌دهندگان → مشاهدات → دانش → هوشمندی → برنامه‌های کاربردی
```

**ممنوع:**
- برنامه‌های کاربردی → ارائه‌دهندگان
- ارائه‌دهندگان → برنامه‌های کاربردی
- استدلال‌گرها → ارائه‌دهندگان
- مشاهدات → هوشمندی
- دانش → رسانه
- زیرساخت اجرا → برنامه‌های کاربردی

**قانون طلایی:** درک به سمت بالا جریان می‌یابد. پیکربندی به سمت پایین جریان می‌یابد. هرگز برعکس.

---

## ۷. مشخصات فنی

### ۷.۱. مشخصات رسانه (Media Specification)

**اصول طراحی:**
- تغییرناپذیر (`frozen=True, slots=True`)
- فقط کتابخانه استاندارد
- انواع صریح
- بدون حالت پنهان
- بدون بارگذاری تنبل

**پروتکل MediaLoader:**

```python
class MediaLoader(Protocol):
    def load(self) -> Media: ...
```

**مدیریت خطا:**
- `MediaNotFoundError` — فایل وجود ندارد
- `UnsupportedMediaError` — پسوند فایل پشتیبانی نمی‌شود
- `InvalidMediaError` — داده رسانه خراب است
- `MediaIOError` — خطای I/O در حین دسترسی

### ۷.۲. مشخصات مشاهده (Artifact Specification)

**فیلدهای پایه:**
- `id` — UUID، خودکار تولید شده
- `kind` — نوع `ArtifactKind`
- `provider` — نام ارائه‌دهنده تولیدکننده
- `created_at` — برچسب زمانی ایجاد UTC
- `payload` — مشاهده واقعی
- `metadata` — متاداتای اختصاصی ارائه‌دهنده
- `parents` — تاپل شناسه‌های UUID

**سریال‌سازی:**

```python
from sceneforge.core.storage import register_artifact_type

@register_artifact_type
@dataclass(frozen=True, slots=True)
class MyArtifact(Artifact[str]):
    confidence: float = 0.0
```

### ۷.۳. مشخصات ارائه‌دهنده (Provider Specification)

**پروتکل Provider (نوع‌دهی ساختاری):**

```python
class Provider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def capabilities(self) -> frozenset[Capability]: ...

    def run(self, media: Media) -> list[Artifact]: ...
```

**کلاس انتزاعی Provider (نوع‌دهی اسمی):**

```python
from abc import ABC, abstractmethod

class Provider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def capabilities(self) -> frozenset[Capability]: ...

    @abstractmethod
    def run(self, media: Media) -> list[Artifact[Any]]: ...
```

**نکته مهم درباره `version`:** `version` بخشی از کلید حافظه نان است. هر زمان که خروجی واقعی ارائه‌دهنده برای ورودی یکسان تغییر کند، آن را افزایش دهید.

### ۷.۴. مشخصات Pipeline

**کلاس Pipeline:**

```python
pipeline = Pipeline(
    provider=FFmpegFrameExtractionProvider(frame_count=12),
    enricher=FFprobeEnricher(),
    store=FileArtifactStore("./cache"),
    max_retries=2,
    retry_backoff_seconds=0.5,
)

# اجرای ساده
artifacts = pipeline.run(media)

# اجرای با جزئیات
result = pipeline.run_detailed(media)
result.artifacts        # list[Artifact]
result.media            # رسانه غنی‌شده
result.duration_seconds # 0.0 اگر از حافظه نان
result.attempts         # 0 اگر از حافظه نان
result.from_cache       # bool
```

**جریان Pipeline:**
1. ایجاد `ProcessingContext` اگر ارائه نشده
2. غنی‌سازی رسانه (اگر `MediaEnricher` تنظیم شده)
3. اعتبارسنجی سازگاری رسانه با قابلیت‌های ارائه‌دهنده
4. بررسی حافظه نان (اگر `ArtifactStore` تنظیم شده)
5. اجرای ارائه‌دهنده (با تلاش‌های مجدد در صورت خطا)
6. ذخیره در حافظه نان (اگر `ArtifactStore` تنظیم شده)
7. بازگشت نتیجه

### ۷.۵. مشخصات افزونه (Plugin Specification)

**کشف افزونه:**

```toml
# در pyproject.toml افزونه:
[project.entry-points."sceneforge.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

```python
# در برنامه میزبان:
from sceneforge.plugins.registry import PluginRegistry

registry = PluginRegistry()
newly_registered = registry.discover()  # همه entry point‌های نصب شده را پیدا می‌کند
```

### ۷.۶. مشخصات ثبت‌نام (Registry Specification)

```python
from sceneforge.core.registry import Registry
from sceneforge.core.capability import Capability

registry = Registry()
registry.register(FFmpegFrameExtractionProvider())
registry.register(PySceneDetectProvider())

# جستجو بر اساس قابلیت
video_capable = registry.by_capability(Capability.DETECT_SCENES)

# دریافت ارائه‌دهنده
provider = registry.get("pyscenedetect")
```

### ۷.۷. مشخصات Runtime

**اجزاء:**
- `ProcessingContext` — وضعیت اجرایی را ذخیره می‌کند
- پشتیبانی از لغو از راه دور
- گزارش پیشرفت
- ارائه متاداتای اجرایی مشترک

```python
from sceneforge.runtime.processing_context import ProcessingContext

context = ProcessingContext()
pipeline.run(media, context=context)
# از thread/Task دیگر:
context.cancel()  # ensure_running() خطا ایجاد می‌کند
```

### ۷.۸. قابلیت‌ها (Capabilities)

```python
class Capability(StrEnum):
    CAPTION = "caption"
    TRANSCRIBE = "transcribe"
    DETECT_SCENES = "detect_scenes"
    OCR = "ocr"
    FACE_DETECTION = "face_detection"
    OBJECT_DETECTION = "object_detection"
    AUDIO_ANALYSIS = "audio_analysis"
    EMBEDDING = "embedding"
    FRAME_EXTRACTION = "frame_extraction"
```

**ثبت‌نام پیش‌فرض:**
- قابلیت‌های تصویر/ویدیو: CAPTION, OCR, FACE_DETECTION, OBJECT_DETECTION
- قابلیت‌های فقط ویدیو: DETECT_SCENES, FRAME_EXTRACTION
- قابلیت‌های صوتی: TRANSCRIBE, AUDIO_ANALYSIS
- قابلیت‌های بین‌رسانه‌ای: EMBEDDING (تصویر، ویدیو، صدا), TRANSCRIBE (صدا، ویدیو)

---

## ۸. سازندگان دانش

### ۸.۱. نمودار وابستگی

```
استخراج فریم (ارائه‌دهنده)
        │
        ▼
SceneGroupingBuilder
    مصرف: FrameExtractionArtifact, SceneCutArtifact, TranscriptSegmentArtifact
    تولید: SceneEntity
    ترتیب: بعد از استخراج فریم، بعد از تشخیص صحنه
        │
        ▼
SceneFaceBuilder
    مصرف: FrameExtractionArtifact, SceneCutArtifact, FaceDetectionArtifact
    تولید: SceneEntity (با داده چهره)
    ترتیب: بعد از استخراج فریم، بعد از تشخیص صحنه، بعد از تشخیص چهره
        │
        ▼
SceneMergeBuilder
    مصرف: SceneEntity (از سازندگان متعدد)
    تولید: SceneEntity (ادغام شده)
    ترتیب: بعد از SceneGroupingBuilder، بعد از SceneFaceBuilder
        │
        ▼
SceneSequenceBuilder
    مصرف: SceneEntity
    تولید: RelationshipEntity
    ترتیب: بعد از SceneMergeBuilder
```

### ۸.۲. SceneGroupingBuilder

فریم‌ها و بخش‌های رونوشت را در بازه‌های زمانی همپوشان گروه‌بندی می‌کند و یک `SceneEntity` برای هر صحنه تشخیص داده شده تولید می‌کند.

**پیاده‌سازی:** `sceneforge/knowledge/scene_grouping_builder.py`

### ۸.۳. SceneFaceBuilder

صحنه‌ها را با داده تشخیص چهره استخراج شده از فریم‌های درون بازه زمانی هر صحنه حاشیه‌نویسی می‌کند.

**پیاده‌سازی:** `sceneforge/knowledge/scene_face_builder.py`

### ۸.۴. SceneMergeBuilder

نمونه‌های `SceneEntity` تولید شده توسط سازندگان مختلف برای یک صحنه را در یک نهاد ادغام شده ترکیب می‌کند.

**پیاده‌سازی:** `sceneforge/knowledge/scene_merge_builder.py`

### ۸.۵. SceneSequenceBuilder

صحنه‌های متوالی را به یک توالی زمانی پیوند می‌دهد و نهادهای رابطه‌ای تولید می‌کند.

**پیاده‌سازی:** `sceneforge/knowledge/relationship_builder.py`

### ۸.۶. EntityStore — ذخیره‌سازی نهادها

```python
from sceneforge.knowledge.storage import FileEntityStore, InMemoryEntityStore

# ذخیره‌سازی فایلی
store = FileEntityStore("./entities")

# ذخیره‌سازی درون‌حافظه‌ای
store = InMemoryEntityStore()

# توابع پرس‌وجو
from sceneforge.knowledge.storage import iter_all_entities, find_related

# همه نهادها
for entity in iter_all_entities(store):
    print(entity.kind, entity.metadata)

# یافتن نهادهای مرتبط
related = find_related(store, entity_id)
```

**اندازه‌گیری عملکرد:**
- ۳۰۰ فیلم مصنوعی × ۲۰ صحنه = ۱۱,۷۰۰ نهاد → `find_related()` در ~0.125 ثانیه
- ۴۰۰ فیلم × ۲۳,۶۰۰ نهاد → تجمیع کامل کتابخانه در ~0.391 ثانیه

---

## ۹. ساختار کد منبع

### ۹.۱. ساختار پوشه‌ها

```
sceneforge/
├── core/                    # انتزاعات پایه
│   ├── artifact.py          # کلاس پایه Artifact
│   ├── async_pipeline.py    # Pipeline ناهمگام
│   ├── async_provider.py    # ارائه‌دهنده ناهمگام
│   ├── cache.py             # ابزارهای حافظه نان
│   ├── capability.py        # enum Capability
│   ├── capability_registry.py # ثبت‌نام قابلیت‌ها
│   ├── enrichment.py        # پروتکل MediaEnricher
│   ├── exceptions.py        # استثنائات
│   ├── identity_artifact.py # Artifact ساده
│   ├── lazy_media.py        # رسانه تنبل
│   ├── naming.py            # قواعد نام‌گذاری
│   ├── pipeline.py          # Pipeline هماهنگ
│   ├── provider.py          # کلاس انتزاعی Provider
│   ├── provider_metadata.py # متاداتای ارائه‌دهنده
│   ├── provider_protocol.py # پروتکل Provider
│   ├── registry.py          # ثبت‌نام ارائه‌دهندگان
│   ├── storage.py           # ArtifactStore
│   └── validation.py        # اعتبارسنجی
├── contrib/                 # ارائه‌دهندگان واقعی
│   ├── audio_info/          # اطلاعات صوتی
│   ├── ffmpeg/              # FFmpeg + FFprobe
│   ├── identity/            # IdentityProvider
│   ├── image_info/          # اطلاعات تصویری
│   ├── media_hash/          # MediaHashProvider
│   ├── opencv/              # تشخیص چهره OpenCV
│   ├── scenedetect/         # تشخیص صحنه PySceneDetect
│   └── whisper/             # رونویسی Whisper
├── knowledge/               # لایه دانش
│   ├── builder.py           # پروتکل KnowledgeBuilder
│   ├── entity.py            # کلاس Entity
│   ├── exceptions.py        # استثنائات دانش
│   ├── relationship_builder.py # پروتکل RelationshipBuilder
│   ├── scene_face_builder.py   # SceneFaceBuilder
│   ├── scene_grouping_builder.py # SceneGroupingBuilder
│   ├── scene_merge_builder.py    # SceneMergeBuilder
│   ├── storage.py           # EntityStore
│   └── validation.py        # اعتبارسنجی دانش
├── media/                   # انواع رسانه
│   ├── base.py              # کلاس پایه Media
│   ├── exceptions.py        # استثنائات رسانه
│   ├── image.py             # ImageMedia
│   ├── image_loader.py      # LocalImageLoader
│   ├── loader.py            # پروتکل MediaLoader
│   ├── video.py             # VideoMedia
│   ├── video_loader.py      # LocalVideoLoader
│   ├── audio.py             # AudioMedia
│   └── audio_loader.py      # LocalAudioLoader
├── plugins/                 # سیستم افزونه
│   ├── plugin.py            # پروتکل Plugin
│   └── registry.py          # PluginRegistry
├── runtime/                 # زیرساخت اجرا
│   ├── media_runtime/       # رمزگشایی رسانه
│   └── processing_context.py # ProcessingContext
└── applications/            # برنامه‌های کاربردی
    └── scene_summary.py     # SceneSummary
```

### ۹.۲. ارائه‌دهندگان موجود (contrib)

#### ۹.۲.۱. FFmpeg (subprocess-backed)

```python
from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher

# استخراج فریم
provider = FFmpegFrameExtractionProvider(frame_count=12)

# غنی‌سازی رسانه
enricher = FFprobeEnricher()

# ترکیب در Pipeline
pipeline = Pipeline(provider=provider, enricher=enricher)
result = pipeline.run_detailed(media)
```

#### ۹.۲.۲. PySceneDetect (الگوریتمی، بدون وزن)

```python
from sceneforge.contrib.scenedetect import PySceneDetectProvider

provider = PySceneDetectProvider(threshold=27.0)
pipeline = Pipeline(provider=provider)
result = pipeline.run_detailed(media)
for cut in result.artifacts:
    print(cut.scene_index, cut.start_seconds, cut.end_seconds)
```

#### ۹.۲.۳. Whisper (مدلی، تزریق وابستگی)

```python
from faster_whisper import WhisperModel
from sceneforge.contrib.whisper import WhisperTranscribeProvider
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.async_pipeline import AsyncPipeline

model = WhisperModel("small", device="cpu", compute_type="int8")
provider = SyncProviderAdapter(WhisperTranscribeProvider(model))
pipeline = AsyncPipeline(provider, max_concurrency=2, timeout_seconds=300)
batch = await pipeline.run_many(scene_audio_clips)
```

#### ۹.۲.۴. OpenCV (الگوریتمی، وزن‌های داخلی)

```python
from sceneforge.contrib.opencv import OpenCVFaceDetectionProvider, OpenCVImageEnricher

provider = OpenCVFaceDetectionProvider()
enricher = OpenCVImageEnricher()
pipeline = Pipeline(provider=provider, enricher=enricher)
result = pipeline.run_detailed(media)
for face in result.artifacts:
    print(face.x, face.y, face.width, face.height)
```

#### ۹.۲.۵. MediaHashProvider

```python
from sceneforge.contrib.media_hash import MediaHashProvider

provider = MediaHashProvider()
pipeline = Pipeline(provider=provider)
result = pipeline.run_detailed(media)
# هش SHA-256 محتوای فایل
```

---

## ۱۰. راهنمای پیاده‌سازی

### ۱۰.۱. نصب و راه‌اندازی

```bash
# کلون مخزن
git clone https://github.com/arianhamid/SceneForge.git
cd SceneForge

# ایجاد محیط مجازی
python -m venv .venv

# فعال‌سازی محیط مجازی
# ویندوز:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# نصب وابستگی‌ها
pip install -e ".[dev]"
```

**وابستگی‌های اختیاری:**

```bash
# تشخیص صحنه
pip install -e ".[scenedetect]"

# رونویسی صدا
pip install -e ".[whisper]"

# تشخیص چهره
pip install -e ".[opencv]"
```

### ۱۰.۲. پیکربندی متغیرهای محیطی

```bash
cp .env .env.local
# فایل .env.local را با تنظیمات خود ویرایش کنید
```

### ۱۰.۳. شروع سریع

```python
from sceneforge.media.video_loader import LocalVideoLoader
from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import FileArtifactStore
from sceneforge.knowledge import SceneGroupingBuilder

# بارگذاری رسانه
media = LocalVideoLoader("movie.mp4").load()
enricher = FFprobeEnricher()
store = FileArtifactStore("./cache")

# استخراج فریم
frames = Pipeline(
    provider=FFmpegFrameExtractionProvider(frame_count=12),
    enricher=enricher,
    store=store,
).run_detailed(media)

# تشخیص صحنه
scenes = Pipeline(
    provider=PySceneDetectProvider(),
    enricher=enricher,
    store=store,
).run_detailed(media)

# لایه دانش: گروه‌بندی فریم‌ها در صحنه‌های مربوطه
entities = SceneGroupingBuilder().build([*frames.artifacts, *scenes.artifacts])
for entity in entities:
    print(entity.metadata["scene_index"], len(entity.metadata["frame_paths"]), "frames")
```

### ۱۰.۴. راهنمای افزودن ارائه‌دهنده جدید

#### مرحله ۱: بررسی قابلیت موجود

```python
from sceneforge.core.capability import Capability
# اگر قابلیت شما قبلاً exists، رد شوید
# در غیر این صورت، آن را به enum Capability اضافه کنید
```

#### مرحله ۲: انتخاب شکل

| نوع ارائه‌دهنده | الگوی کپی | نیاز به تزریق وابستگی |
|-----------------|-----------|----------------------|
| ابزار CLI (ffmpeg) | `sceneforge.contrib.ffmpeg` | خیر |
| الگوریتم خالص (scenedetect) | `sceneforge.contrib.scenedetect` | خیر |
| مدل با وزن‌های داخلی (OpenCV) | `sceneforge.contrib.opencv` | خیر |
| مدل با وزن‌های دانلودی (Whisper) | `sceneforge.contrib.whisper` | **بله** |

#### مرحله ۳: تزریق مدل (اگر نیاز است)

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MyModelProtocol(Protocol):
    def infer(self, input_path: str) -> MyModelOutput: ...

class MyProvider(Provider):
    def __init__(self, model: MyModelProtocol) -> None:
        self._model = model
    # ...
```

#### مرحله ۴: نوشتن مشاهده

```python
from sceneforge.core.storage import register_artifact_type

@register_artifact_type
@dataclass(frozen=True, slots=True)
class MyArtifact(Artifact[PayloadType]):
    media_id: UUID = field(default_factory=uuid4)
    # فیلدهای اختصاصی...
    kind: ArtifactKind = ArtifactKind.SOMETHING
    provider: str = "my_provider"
```

#### مرحله ۵: نوشتن ارائه‌دهنده

```python
class MyProvider(Provider):
    @property
    def name(self) -> str:
        return "my_provider"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.MY_CAPABILITY})

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, ExpectedMediaType):
            raise TypeError(f"Expected ExpectedMediaType, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError("...")

        try:
            result = self._model.infer(str(source))
        except Exception as exc:
            raise ProviderError(f"...: {exc}") from exc

        return [MyArtifact(media_id=media.id, provider=self.name, ...)]
```

#### مرحله ۶: برای ارائه‌دهندگان کند

```python
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.async_pipeline import AsyncPipeline

pipeline = AsyncPipeline(SyncProviderAdapter(MyProvider(model)), max_concurrency=3)
batch = await pipeline.run_many(media_items)
```

#### مرحله ۷: تست‌ها

- یک تست برای هر حالت خطا
- یک تست برای مسیر خوشحال
- تست‌های واحد با مدل جعلی
- تست یکپارچه با ابزار واقعی (در صورت امکان)
- تست از طریق Pipeline/AsyncPipeline

#### مرحله ۸: به‌روزرسانی مستندات

- `docs/specifications/PROVIDER_SPEC.md`
- `docs/architecture/DOMAIN_MODEL.md`
- `pyproject.toml`
- `.ai/PROJECT_STATE.md`
- `.ai/NEXT_TASK.md`

### ۱۰.۵. الگوهای رایج

#### الگوی ۱: تحلیل کامل ویدیو

```python
from sceneforge.media.video_loader import LocalVideoLoader
from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import FileArtifactStore
from sceneforge.knowledge import SceneGroupingBuilder

media = LocalVideoLoader("movie.mp4").load()
enricher = FFprobeEnricher()
store = FileArtifactStore("./cache")

# استخراج فریم
frames = Pipeline(
    provider=FFmpegFrameExtractionProvider(frame_count=12),
    enricher=enricher,
    store=store,
).run_detailed(media)

# تشخیص صحنه
scenes = Pipeline(
    provider=PySceneDetectProvider(),
    enricher=enricher,
    store=store,
).run_detailed(media)

# گروه‌بندی صحنه‌ها
entities = SceneGroupingBuilder().build([*frames.artifacts, *scenes.artifacts])
```

#### الگوی ۲: تشخیص چهره در تصویر

```python
from sceneforge.media.image_loader import LocalImageLoader
from sceneforge.contrib.opencv import OpenCVFaceDetectionProvider, OpenCVImageEnricher
from sceneforge.core.pipeline import Pipeline

media = LocalImageLoader("photo.jpg").load()
pipeline = Pipeline(
    provider=OpenCVFaceDetectionProvider(),
    enricher=OpenCVImageEnricher(),
)
result = pipeline.run_detailed(media)
for face in result.artifacts:
    print(f"Face at ({face.x}, {face.y}), size {face.width}x{face.height}")
```

#### الگوی ۳: رونویسی صدا

```python
from faster_whisper import WhisperModel
from sceneforge.contrib.whisper import WhisperTranscribeProvider
from sceneforge.core.async_provider import SyncProviderAdapter

model = WhisperModel("small", device="cpu", compute_type="int8")
provider = SyncProviderAdapter(WhisperTranscribeProvider(model))

# برای هر قطعه صوتی
transcript = provider.run(audio_media)
```

#### الگوی ۴: استفاده از SceneSummary

```python
from sceneforge.knowledge.storage import InMemoryEntityStore
from sceneforge.applications.scene_summary import SceneSummary

store = InMemoryEntityStore()
# ... پر کردن store با نهادهای صحنه ...

summary = SceneSummary(store)
data, markdown = summary.generate()
print(markdown)
```

---

## ۱۱. تست‌ها و کیفیت کد

### ۱۱.۱. اجرای تست‌ها

```bash
# اجرای همه تست‌ها
pytest tests/ -v

# اجرای تست‌ها با پوشش
pytest tests/ --cov=sceneforge --cov-report=html
```

### ۱۱.۲. بررسی کیفیت کد

```bash
# بررسی linting
ruff check sceneforge/

# قالب‌بندی کد
ruff format sceneforge/

# بررسی نوع
mypy sceneforge/
```

### ۱۱.۳. آمار فعلی

- **تعداد تست‌ها:** ۳۱۵+
- **فایل‌های منبع:** ۷۹
- **mypy --strict:** بدون خطا
- **ruff check:** تمام بررسی‌ها موفق

### ۱۱.۴. انواع تست‌ها

| نوع | توضیح | مثال |
|------|--------|------|
| تست واحد | تست توابع و کلاس‌ها به صورت جداگانه | `tests/contrib/test_whisper_transcribe.py` |
| تست یکپارچه | تست جریان کامل با ابزارهای واقعی | `tests/contrib/test_ffmpeg_integration.py` |
| تست مقیاس | تست عملکرد در مقیاس واقعی | `tests/knowledge/test_scale_spike.py` |
| تست معماری | اجرای قوانین وابستگی | `tests/architecture/test_dependency_rules.py` |

---

## ۱۲. ثبت تصمیمات معماری (ADR)

### ۱۲.۱. فهرست ADRها

| شماره | عنوان | وضعیت |
|--------|-------|-------|
| 0001 | پروتکل ارائه‌دهنده | بسته شده |
| 0002 | تغییرناپذیری رسانه | بسته شده |
| 0003 | ارکستراسیون Pipeline | بسته شده |
| 0004 | بازنمایی‌های اجرا | بسته شده |
| 0005 | اعتبارسنجی قابلیت | بسته شده |
| 0006 | کامل بودن پروتکل ارائه‌دهنده | بسته شده |
| 0007 | ثبت‌نام قابلیت تزریق‌پذیر | بسته شده |
| 0008 | پایداری مشاهدات | بسته شده |
| 0009 | ارائه‌دهندگان ناهمگام | بسته شده |
| 0010 | ارائه‌دهندگان مدلی با تزریق وابستگی | بسته شده |
| 0011 | دامنه اولین سازنده دانش | بسته شده |
| 0012 | پایداری نهادها | بسته شده |
| 0013 | روابط نهادها | بسته شده |
| 0014 | پرس‌وجوی رابطه (اندازه‌گیری مقیاس) | بسته شده |
| 0015 | تشخیص چهره OpenCV | بسته شده |
| 0016 | سازنده دانش بین‌دامنه‌ای | بسته شده |
| 0017 | اتصال Registry/Pipeline (بسته شده) | بسته شده |
| 0018 | سازنده ادغام صحنه | بسته شده |
| 0019 | پرس‌وجوی بین‌ویدیویی (اندازه‌گیری مقیاس) | بسته شده |
| 0020 | سطح API پایدار | بسته شده |

### ۱۲.۲. تصمیمات کلیدی

**ADR-0012: پایداری نهادها**
- EntityStore جداگانه، نه یک generic مشترک با ArtifactStore
- دلیل: نام فیلدها متفاوت است (`Entity.builder` vs `Artifact.provider`)
- کلید کش بر اساس مجموعه دقیق شناسه‌های مشاهدات ورودی

**ADR-0014: پرس‌وجوی رابطه**
- `find_related()` در ~0.125s روی ۱۱,۷۰۰ نهاد
- نیازی به ایندکس، backend متفاوت یا کتابخانه گراف نیست

**ADR-0019: پرس‌وجوی بین‌ویدیویی**
- تجمیع کامل کتابخانه ۴۰۰ فیلمی در ~0.391s
- چهار اندازه‌گیری متوالی نشان داده Entity/EntityStore کافی است

---

## ۱۳. مشارکت در پروژه

### ۱۳.۱. حوزه‌های مشارکت

- بینایی ماشین
- مدل‌های زبانی بزرگ
- درک ویدیو
- گراف‌های دانش
- معماری نرم‌افزار
- متن‌باز

### ۱۳.۲. فرآیند Pull Request

هر PR باید:
- شامل تست باشد (در صورت صدق)
- مستندات را به‌روزرسانی کند
- معماری را نشکند
- از `STYLE_GUIDE.md` و `NAMING_CONVENTIONS.md` پیروی کند
- قبل از ارسال `ruff check --fix`، `ruff format` و `mypy --strict` را اجرا کند

### ۱۳.۳. قوانین نام‌گذاری

- فایل‌ها: `snake_case.py`
- کلاس‌ها: `PascalCase`
- توابع/متغیرها: `snake_case`
- ثابت‌ها: `UPPER_SNAKE_CASE`

---

## ۱۴. وضعیت فعلی پروژه

### ۱۴.۱. تکمیل شده

- لایه‌های ۰-۳ (رسانه، زیرساخت اجرا، ارائه‌دهندگان، مشاهدات) پیاده‌سازی و تست شده
- ۴ ارائه‌دهنده واقعی در ۲ حوزه قابلیت
- ۳ سازنده دانش واقعی + ۱ سازنده رابطه
- EntityStore در ۴ اندازه‌گیری مختلف کافی تشخیص داده شده
- نمونه اجرای end-to-end قابل اجرا
- مستندات جامع

### ۱۴.۲. در حال توسعه (Sprint 12)

- اولین برنامه کاربردی واقعی: SceneSummary
- MediaHashProvider
- ArtifactCategory
- Provenance تایپ شده
- اعتبارسنجی دانش ساختاریافته
- تست‌های معماری

### ۱۴.۳. مشکلات شناخته شده

- لایه‌های ۵-۷ به عنوان زیرساخت مجزا وجود ندارند
- ترکیب Pipeline وجود ندارد
- `FileArtifactStore`/`FileEntityStore` ساده هستند (JSON در هر کلید)
- `WhisperTranscribeProvider` با وزن‌های واقعی تست نشده
- `OpenCVFaceDetectionProvider` با عکس واقعی تست نشده
- `CAPTION`/`OCR`/`OBJECT_DETECTION` بدون پیاده‌سازی واقعی

### ۱۴.۴. ایده‌های آینده

- CLI: `sceneforge run <file> --providers frame_extraction,detect_scenes,face_detection`
- پشتیبانی SQLite برای ArtifactStore/EntityStore
- آشکارساز چهره مبتنی بر DNN
- ارائه‌دهنده سوم حوزه قابلیت (CAPTION/OCR)

---

## ۱۵. واژه‌نامه فنی

| اصطلاح | تعریف |
|--------|-------|
| **Artifact** | مشاهده استخراج شده از رسانه توسط ارائه‌دهنده. تغییرناپذیر، قابل سریال‌سازی |
| **ArtifactStore** | پایداری محتوای آدرس‌پذیر برای مشاهدات، کلیدگذاری‌شده بر اساس هویت رسانه + نام ارائه‌دهنده + نسخه |
| **Media** | شیء منبعی که ارائه‌دهنده روی آن عمل می‌کند. تغییرناپذیر؛ از طریق `evolve()` اصلاح می‌شود |
| **MediaEnricher** | متاداتای جایگزین رسانه را به متاداتای معتبر تبدیل می‌کند |
| **Capability** | ویژگی نام‌گذاری شده چارچوب که کد به جای مدل یا کتابخانه خاص به آن وابسته است |
| **Knowledge** | واقعیت‌های استخراج‌شده از چندین مشاهده |
| **Reasoning** | روابط استنتاج‌شده از دانش |
| **Application** | مصرف‌کننده دانش |
| **Provider** | تولیدکننده مشاهدات. یک یا چند قابلیت را پیاده‌سازی می‌کند |
| **Pipeline** | هماهنگ‌کننده برای اجرای یک ارائه‌دهنده روی یک شیء رسانه |
| **Plugin** | بسته‌ای که چارچوب را گسترش می‌دهد، از طریق `importlib.metadata.entry_points()` قابل کشف |
| **Entity** | مفهوم قابل بازیابی مشتق شده از مشاهدات |
| **KnowledgeBuilder** | مشاهدات را به نهادها تبدیل می‌کند |
| **RelationshipBuilder** | نهادها را به روابط تبدیل می‌کند |
| **EntityStore** | حافظه نان خروجی سازندگان دانش |
| **ProcessingContext** | وضعیت اجرایی را ذخیره می‌کند، لغو را پشتیبانی می‌کند |
| **Provenance** | اطلاعات منشأ نهاد (سازنده، شناسه‌های مشاهدات منبع، اطمینان) |

---

## پیوست

### الف. لینک‌های مفید

- [مرور معماری](docs/architecture/OVERVIEW.md)
- [مدل دامنه](docs/architecture/DOMAIN_MODEL.md)
- [معماری لایه‌ای](docs/architecture/LAYERS.md)
- [چشم‌انداز](docs/philosophy/VISION.md)
- [ضد-اهداف](docs/philosophy/ANTI_GOALS.md)
- [راهنمای افزودن ارائه‌دهنده](docs/guides/ADDING_A_PROVIDER.md)
- [مشخصات رسانه](docs/specifications/MEDIA_SPEC.md)
- [مشخصات مشاهده](docs/specifications/ARTIFACT_SPEC.md)
- [مشخصات ارائه‌دهنده](docs/specifications/PROVIDER_SPEC.md)
- [مشخصات افزونه](docs/specifications/PLUGIN_SPEC.md)
- [مشخصات ثبت‌نام](docs/specifications/REGISTRY_SPEC.md)
- [مشخصات Runtime](docs/specifications/RUNTIME_SPEC.md)

### ب. نمونه کد قابل اجرا

فایل نمونه کامل: `examples/end_to_end/analyze_video.py`

### ج. مستندات معماری

فهرست کامل ADRها در: `docs/adr/`

---

> **فیلم‌ها فقط ویدیو نیستند. آن‌ها دنیاهایی هستند که منتظر درک شدن‌اند.**
