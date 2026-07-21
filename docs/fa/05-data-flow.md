# ۵. جریان کامل داده — از فایل ویدیو تا دانش

در این فایل، اسکریپت واقعی `examples/end_to_end/analyze_video.py` را قدم‌به‌قدم دنبال می‌کنیم. این بهترین راه برای فهمیدن این است که همه‌ی مفاهیمی که تا الان خواندی، چطور کنار هم کار می‌کنند.

می‌توانی خودت این اسکریپت را اجرا کنی (نیاز به نصب `ffmpeg` و پکیج `scenedetect` دارد):

```bash
python examples/end_to_end/analyze_video.py path/to/movie.mp4
```

## قدم ۱: بارگذاری فایل ویدیو

```python
media = LocalVideoLoader(video_path).load()
print(f"Loaded {media.name} (placeholder duration={media.duration})")
```

اینجا `media` یک شیء `VideoMedia` است، اما `duration` آن هنوز `0.0` است — چون (طبق فایل ۴) بارگذاری اولیه سبک است و فایل واقعاً رمزگشایی نشده.

## قدم ۲: ساختن ابزارهای مشترک

```python
enricher = FFprobeEnricher()
store = FileArtifactStore(cache_dir)
```

`enricher` بعداً اطلاعات واقعی ویدیو (مدت‌زمان، codec، فریم‌ریت) را پر می‌کند. `store` محل ذخیره‌ی کش روی دیسک است — یک پوشه با فایل‌های JSON.

## قدم ۳: ساختن دو Pipeline جداگانه

```python
frame_pipeline = Pipeline(
    provider=FFmpegFrameExtractionProvider(frame_count=8, output_dir=frames_dir),
    enricher=enricher,
    store=store,
    max_retries=1,
)
scene_pipeline = Pipeline(
    provider=PySceneDetectProvider(), enricher=enricher, store=store
)
```

همان‌طور که در فایل ۲ گفتیم، هر `Pipeline` فقط با یک Provider کار می‌کند. اینجا دو `Pipeline` جدا داریم — یکی برای استخراج قاب، یکی برای تشخیص صحنه — و هر دو از همان `enricher` و همان `store` استفاده می‌کنند (برای هماهنگی).

## قدم ۴: اجرای واقعی

```python
frame_result = frame_pipeline.run_detailed(media)
scene_result = scene_pipeline.run_detailed(media)
```

اینجا واقعاً اتفاق می‌افتد:

1. `enricher.enrich(media)` صدا زده می‌شود → یک `VideoMedia` جدید با اطلاعات واقعی برمی‌گردد.
2. `Pipeline` بررسی می‌کند آیا نتیجه‌ی این Provider روی این ویدیو قبلاً در `store` هست یا نه.
3. اگر نبود، `provider.run(enriched_media)` اجرا می‌شود — یعنی دستور واقعی `ffmpeg` روی سیستم اجرا می‌شود و چند فایل PNG در `frames_dir` ساخته می‌شود.
4. نتیجه (لیستی از `FrameExtractionArtifact`) در `store` ذخیره می‌شود.
5. یک `PipelineResult` برمی‌گردد که شامل `artifacts`، `media` (نسخه‌ی غنی‌شده)، `duration_seconds`، و `from_cache` است.

برای صحنه‌ها هم دقیقاً همین اتفاق می‌افتد، اما با اجرای واقعی کتابخانه‌ی `scenedetect`.

## قدم ۵: ساختن دانش از Artifact ها

```python
knowledge_artifacts = [*frame_result.artifacts, *scene_result.artifacts]
entities = build_with_cache(SceneGroupingBuilder(), knowledge_artifacts, entity_store)
```

اینجا لیست Artifact های خام (قاب‌ها + برش‌های صحنه) به `SceneGroupingBuilder` داده می‌شود. این کلاس:

1. `SceneCutArtifact` ها را پیدا می‌کند (این‌ها مرزهای هر صحنه را مشخص می‌کنند).
2. هر `FrameExtractionArtifact` را، بر اساس `timestamp_seconds`اش، به صحنه‌ی درست نسبت می‌دهد.
3. یک `Entity` جدید برای هر صحنه می‌سازد که در `metadata` خودش، مسیر قاب‌های آن صحنه را نگه می‌دارد.

`build_with_cache` دقیقاً همان‌کاری را برای Entity ها می‌کند که `Pipeline` برای Artifact ها می‌کند: قبل از اجرا، کش را چک می‌کند.

## قدم ۶: روابط بین صحنه‌ها

```python
relationships = SceneSequenceBuilder().relate(entities)
```

اینجا ورودی دیگر Artifact نیست — خودِ `entities` (که در قدم قبل ساختیم) است. `SceneSequenceBuilder` یک Entity جدید از نوع «رابطه» می‌سازد که می‌گوید «صحنه‌ی ۰ قبل از صحنه‌ی ۱ است».

## قدم ۷ (اختیاری): تشخیص چهره در هر قاب

```python
for frame_artifact in frame_result.artifacts:
    frame_media = LocalImageLoader(frame_artifact.frame_path).load()
    face_artifacts.extend(face_pipeline.run(frame_media))
```

اینجا یک نکته‌ی ظریف هست: هر قابِ استخراج‌شده (که یک فایل PNG روی دیسک است) دوباره به‌عنوان یک `ImageMedia` **جدید** بارگذاری می‌شود. یعنی این تصویر یک `media_id` کاملاً جدید می‌گیرد که ربطی به `media_id` ویدیوی اصلی ندارد.

سؤال: پس چطور بعداً می‌فهمیم این چهره‌ی تشخیص‌داده‌شده مال کدام صحنه است؟ جواب در `source_frame_path` است — وقتی `OpenCVFaceDetectionProvider` اجرا می‌شود، مسیر همان فایل تصویر را در `FaceDetectionArtifact.source_frame_path` ذخیره می‌کند. این مسیر دقیقاً همان `frame_path`ی است که در `FrameExtractionArtifact` هم بود. پس دو Artifact «بدون این‌که `media_id`شان یکی باشد» با هم مرتبط می‌شوند — فقط چون هر دو یک مسیر فایل مشترک را می‌شناسند.

این الگو دقیقاً همان چیزی است که `SceneFaceBuilder` استفاده می‌کند تا چهره‌ها را به صحنه‌ی درست نسبت دهد — و بعداً همین الگو برای تشخیص متن (`SceneTextBuilder`) هم دوباره استفاده شد، بدون هیچ تغییری.

## قدم ۸: ادغام چند سازنده‌ی دانش با هم

```python
merged = SceneMergeBuilder().relate([*entities, *face_entities])
```

حالا دو Entity جداگانه داریم که هر دو درباره‌ی «صحنه‌ی ۰» هستند — یکی از `SceneGroupingBuilder` (با دیالوگ)، یکی از `SceneFaceBuilder` (با تعداد چهره). `SceneMergeBuilder` این دو را به یک Entity واحد ترکیب می‌کند، اما داده‌ی هر سازنده را زیر یک کلید جداگانه (به نام همان سازنده) نگه می‌دارد — تا هیچ‌وقت دو سازنده به‌طور تصادفی روی داده‌ی هم ننویسند.

## قدم ۹: اثبات این‌که کش واقعاً کار می‌کند

```python
second_frames = frame_pipeline.run_detailed(media)
print(f"frames from_cache={second_frames.from_cache}")  # باید True باشد
```

اگر همان اسکریپت را دوباره روی همان ویدیو اجرا کنی، `ffmpeg` دوباره اجرا **نمی‌شود** — نتیجه از فایل‌های JSON کش خوانده می‌شود. این دقیقاً همان وعده‌ی «هر فیلم فقط یک‌بار تحلیل می‌شود» است که در فایل ۱ توضیح دادیم — و اینجا می‌توانی با چشم خودت ببینی که واقعی است.

## خلاصه‌ی کل مسیر

```
فایل ویدیو
   │  LocalVideoLoader.load()
   ▼
Media (اطلاعات جایگزین)
   │  FFprobeEnricher.enrich()
   ▼
Media (اطلاعات واقعی)
   │  Pipeline با Providerهای مختلف
   ▼
Artifact ها (قاب، برش صحنه، چهره، متن)
   │  KnowledgeBuilder.build()
   ▼
Entity ها (یک Entity برای هر صحنه)
   │  RelationshipBuilder.relate()
   ▼
Entity های ترکیبی/رابطه‌ای (ترتیب صحنه‌ها، ادغام چند سازنده)
   │  ذخیره در EntityStore
   ▼
یک برنامه‌ی واقعی (مثل SceneSummary) این‌ها را می‌خواند
   ▼
خروجی قابل‌استفاده برای انسان
```

---

مرحله‌ی بعد: [`06-providers-guide.md`](06-providers-guide.md) — حالا بیایید هرکدام از پنج Provider واقعی را از نزدیک ببینیم.
