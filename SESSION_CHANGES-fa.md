<div dir="rtl">
# تغییرات نشست: فاز صفر ADR-0024 تا فاز یک (سطح Facts)

خلاصهٔ تمام کارهایی که در این نشست انجام شد، به ترتیب زمانی. این متن برای
استفاده به‌عنوان پیام commit یا توضیح Pull Request نوشته شده است؛ هر بخش تقریباً
با یک commit منطقی مطابقت دارد و در صورت نیاز می‌توان آن‌ها را جدا کرد.

---

## ۱. بررسی و اصلاح بازبینی پیاده‌سازی ۲۰۲۶-۰۷-۲۲

- مهم‌ترین یافته‌های بازبینی به‌صورت واقعی بازتولید شد: استفاده از `Media.id`
  تصادفی در `content_key()`، غیرقابل‌سریال‌سازی بودن `Provenance` و قابل‌تغییر
  بودن metadataهای تو‌در‌تو. پیش از اعتماد به نتایج، هر سه مورد بررسی شد.
- مشکل **رفت‌وبرگشت provenance** اصلاح شد: توابع `entity_to_dict` و
  `entity_from_dict` در `sceneforge/knowledge/storage.py` اکنون `Provenance` را
  به‌درستی serialize/deserialize می‌کنند؛ پیش‌تر ذخیره‌سازی با `TypeError`
  شکست می‌خورد.
- **ADR-0024** با عنوان «فاز صفر — هویت قابل‌اعتماد، شواهد و منشأ اجرای تحلیل»
  نوشته شد. این ADR پنج خروجی را پیش از providerهای captioning و
  object-detection (که ابتدا برای فاز یک برنامه‌ریزی شده بودند) تعریف می‌کند.
- یک بازبینی مستقلِ بعدی، چند نقص را پیدا کرد که اصلاح شدند: تست‌های ضعیفِ
  round-trip که واقعاً JSON serialization را اجرا نمی‌کردند، نبود ترجمهٔ خطا در
  مرز دادهٔ خراب provenance، ناهماهنگی «چهار بخش» در برابر پنج مورد در ADR، و
  تعریف ناکافی endpointهای `EvidenceLink`.

## ۲. فاز صفر ADR-0024 — هر پنج مورد تحویل شد

1. **Provenance از طریق `EntityStore` رفت‌وبرگشت دارد.** (در بخش قبل توضیح داده
   شد.)
2. **طراحی دوبارهٔ `content_key()`**: شناسهٔ تصادفی `Media.id` برای هر بار بارگذاری
   با هویت واقعی محتوا جایگزین شد؛ این هویت از hash بایت‌های فایل به‌دست می‌آید
   و برای media بدون فایل پشتیبان، fallback مستندِ مبتنی بر نام دارد. همچنین
   property جدید `Provider.execution_fingerprint` در cache key وارد شد.
   `WhisperTranscribeProvider` آن را با hash مربوط به `transcribe_kwargs`
   بازنویسی می‌کند؛ این همان مورد برخوردی است که بازبینی قبلی در عمل پیدا کرده
   بود. این تغییر عمداً cacheهای قدیمی را نامعتبر می‌کند.
3. **قرارداد typed برای شواهد**: فایل جدید
   `sceneforge/core/evidence.py` شامل `EvidenceAnchor`، `EvidenceLink`،
   `Reference` و `ReferenceKind` و `EvidenceRelation` است. همچنین
   `ArtifactStore.keys()` و توابع `find_artifact_by_id()` و
   `find_artifacts_by_media()` در `core/storage.py` اضافه شدند.
4. **تفکیک cache از evidence**: نوع جدید `KnowledgeRecordStore` در
   `sceneforge/knowledge/storage.py` اضافه شد؛ شامل
   `FileKnowledgeRecordStore` و `InMemoryKnowledgeRecordStore`. این store
   پایدار، append-only و revision-aware است و از نقش cache قابل‌حذفِ
   `EntityStore` جداست. فقط `append()` و `retract()` دارد و `put` یا `delete`
   ندارد.
5. **مانیفست `AnalysisRun`**: فایل جدید
   `sceneforge/runtime/analysis_run.py` شامل `AnalysisRun`، `StageRecord` و
   `StageOutcome` است. این قابلیت به‌صورت opt-in با پارامتر `analysis_run` به
   `Pipeline.run_detailed()` و `AsyncPipeline.run_detailed()`/`run_many()` وصل
   شد. وضعیت‌های `ATTEMPTED`، `SKIPPED` و `FAILED`، همراه با cache hit، اجرای
   تازه، retry و duration ثبت می‌شوند؛ وقتی این پارامتر حذف شود، رفتار قبلیِ
   return/raise تغییر نمی‌کند.

هر پنج مورد با تست‌های unit و integration اثبات شدند و پس از هر مرحله با
`pytest`، `ruff` و `mypy --strict` بررسی شدند.

## ۳. فاز یک — سطح Facts با دو ورودی واقعی مستقل

- **`TransformersCaptionProvider`** در
  `sceneforge/contrib/transformers_caption/` پیاده‌سازی واقعی
  `Capability.CAPTION` است و یک pipeline تزریق‌شدهٔ Hugging Face
  `transformers` از نوع `image-text-to-text` را wrap می‌کند. الگوی
  dependency injection آن با `WhisperTranscribeProvider` یکسان است. پروتکل
  `ImageTextToTextPipelineProtocol` بر اساس source واقعی نسخهٔ نصب‌شدهٔ
  `transformers==5.14.1` طراحی شد، نه بر اساس حدس.
- **`TransformersObjectDetectionProvider`** در
  `sceneforge/contrib/transformers_object_detection/` دومین provider واقعیِ
  سطح Facts است و برای آزمودن عمومی‌بودن شکل Fact extraction ساخته شد. تفاوت
  مهم طراحی این بود که نتیجهٔ خالی در object detection معتبر است، اما caption
  خالی معتبر نیست.
- **`FactExtractionBuilder`** در
  `sceneforge/knowledge/fact_extraction_builder.py` (به‌همراه
  `EntityKind.FACT`) هر یک از این دو artifact را به یک Entity از نوع `Fact`
  تبدیل می‌کند. الگوی تعداد artifact («یک Artifact ← یک Fact») برای هر دو
  provider عمومی شد، اما منطق ساخت متن statement عمومی نشد و بر اساس نوع
  artifact dispatch می‌کند. `Provenance.confidence` برای نخستین بار یک مقدار
  واقعی و غیر `None` از scoreهای detection گرفت.
- این مسیر از ابتدا تا انتها با یک تصویر واقعی ساخته‌شده توسط **ffmpeg**، نه
  فقط fakeها، اثبات شد: `tests/knowledge/test_fact_extraction_integration.py`.
- **`SceneSummary`** در `sceneforge/applications/scene_summary.py` گسترش یافت
  تا Facts را در بخش مستقل خود render کند. برای نخستین بار زنجیرهٔ provider تا
  خروجی قابل مشاهده کامل شد. این قابلیت برای Facts حاصل از object detection
  بدون تغییر کد اضافی نیز کار کرد.

## ۴. باگ‌هایی که در مسیر پیدا و اصلاح شدند

- `TransformersObjectDetectionProvider` فیلد
  `ObjectDetectionArtifact.source_frame_path` را اعلام کرده بود اما هرگز آن
  را مقداردهی نمی‌کرد و مقدار همیشه بی‌صدا `""` بود.
- `CaptionArtifact` برخلاف سه artifact تشخیصِ فریم‌محور دیگر
  (`FaceDetectionArtifact`، `OCRTextArtifact` و `ObjectDetectionArtifact`)،
  فیلد `source_frame_path` نداشت. این فیلد اضافه و مقداردهی شد و سپس از طریق
  `FactExtractionBuilder` به metadata مربوط به Fact رسید.
- docstring فایل `sceneforge/contrib/tesseract/__init__.py` ادعا می‌کرد OCR
  «نخستین قابلیت واقعی برای سطح Facts» است؛ این ادعا با عنوان صریح ADR-0022
  («Still Evidence Not Facts») تناقض داشت و اصلاح شد.
- `examples/end_to_end/analyze_video.py` وقتی `transformers` نصب بود اما وزن
  مدل قابل دریافت نبود، با `OSError` مدیریت‌نشده متوقف می‌شد. این مشکل با اجرای
  واقعی اسکریپت روی ویدیوی ساخته‌شده با ffmpeg پیدا شد، نه صرفاً با خواندن کد.
  نگهبان `try/except ImportError` فقط importها را پوشش می‌داد؛ اکنون اطراف
  ساخت مدل نیز exception guard گسترده‌تری قرار گرفته تا مانند سایر مراحل
  اختیاری، اجرای کلی graceful skip شود.
- دو مورد تکراری در مستندات `.ai/PROJECT_STATE.md` حذف و ادغام شد: bullet مربوط
  به تعداد providerهای واقعی و bullet مربوط به تأییدنشدن وزن‌های دانلودی.

## ۵. گسترش `examples/end_to_end/analyze_video.py`

موارد زیر اضافه شدند؛ هرکدام اختیاری‌اند و اگر در دسترس نباشند با پیام واضح
نادیده گرفته می‌شوند:

- OCR واقعی با Tesseract (`TesseractOCRProvider` و `SceneTextBuilder`)
- captioning و object detection واقعی، یعنی مرحلهٔ سطح Facts، با flag جدید
  `--no-facts`؛ زیرا این تنها مرحله‌ای است که به دسترسی شبکه به Hugging Face
  Hub نیاز دارد
- render نهایی `SceneSummary` که scenes و Facts را هم‌زمان نشان می‌دهد
- گسترش بخش «دو بار اجرا کن و کارکرد cache را ثابت کن» برای cacheهای جدید

این اسکریپت با یک ویدیوی واقعی ساخته‌شده توسط ffmpeg در همین محیط اجرا و بررسی
شد؛ صرفاً syntax-check نشد.

## ۶. مستندات

هر مرحله با به‌روزرسانی `.ai/PROJECT_STATE.md`، `.ai/NEXT_TASK.md`، بخش
Understanding Ladder در `docs/architecture/DOMAIN_MODEL.md` و
`docs/specifications/PROVIDER_SPEC.md` همراه شد. پس از هر تغییر بزرگ، جست‌وجوی
کامل برای ارجاع‌های قدیمی انجام شد؛ از جمله اصلاح چند ناهماهنگی قبلی که مستقیماً
مربوط به این نشست نبودند: تعداد قدیمی providerها و ادعای قدیمیِ «مسدود بودن روی
Facts» در ورودی Events، که اکنون با واقعی‌شدن Facts دیگر درست نیست.

---

## بررسی نهایی

```text
516 passed, 1 skipped
ruff check: all checks passed
ruff format --check: all files formatted
mypy --strict: no issues found in 92 source files
```

## سطح جدید API عمومی

- `sceneforge.core`: `EvidenceAnchor`، `EvidenceLink`، `EvidenceRelation`,
  `Reference`، `ReferenceKind`، `find_artifact_by_id` و
  `find_artifacts_by_media`
- `sceneforge.knowledge`: `FactExtractionBuilder`، `KnowledgeRecord`،
  `KnowledgeRecordStore`، `FileKnowledgeRecordStore`،
  `InMemoryKnowledgeRecordStore` و `EntityKind.FACT`
- `sceneforge.runtime`: `AnalysisRun`، `StageRecord` و `StageOutcome`
- `sceneforge.contrib.transformers_caption`: `CaptionArtifact`،
  `TransformersCaptionProvider` و `ImageTextToTextPipelineProtocol`
- `sceneforge.contrib.transformers_object_detection`:
  `ObjectDetectionArtifact`، `TransformersObjectDetectionProvider` و
  `ObjectDetectionPipelineProtocol`
- `Provider.execution_fingerprint`؛ property جدید روی ABC و هر دو پروتکل
  structural یعنی `Provider` و `AsyncProvider`
- `ArtifactStore.keys()`؛ عضو جدید پروتکل

## تغییرات ناسازگار

- `content_key()` پارامتر چهارم جدیدی به نام `execution_fingerprint` گرفته است
  که مقدار پیش‌فرض آن `""` است و بنابراین از نظر فراخوانی backward-compatible
  محسوب می‌شود؛ اما مبنای هویت آن تغییر کرده است. **cacheهای محلی موجود
  invalid می‌شوند و migrate نمی‌شوند.** این تصمیم در ADR-0024، مورد دوم، عمداً
  گرفته شده و oversight نبوده است.
