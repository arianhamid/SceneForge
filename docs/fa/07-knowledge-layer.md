# ۷. لایه‌ی دانش — از Artifact تا فهمیدن

## Entity چیست؟

`Entity` معادل `Artifact` در لایه‌ی دانش است — اما با یک فرق مهم: `Artifact` نتیجه‌ی *یک* Provider است، `Entity` نتیجه‌ی *ترکیب چند* Artifact (احتمالاً از چند Provider مختلف) است.

```python
@dataclass(frozen=True, slots=True)
class Entity[T]:
    id: UUID = field(default_factory=uuid4)
    kind: EntityKind = EntityKind.ENTITY
    builder: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: T = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    parents: tuple[UUID, ...] = ()
    provenance: Provenance | None = None
```

خیلی شبیه `Artifact` است، عمداً — همان انضباط غیرقابل‌تغییری، همان `parents` برای ردیابی منشأ. البته این تغییرناپذیری فعلاً سطحی است: خودِ mapping عوض نمی‌شود، اما یک لیست/دیکشنری تودرتو در `metadata` هنوز قابل‌تغییر است؛ این محدودیت پایین‌تر توضیح داده می‌شود.

## شش Builder واقعی: چهار Knowledge Builder و دو Relationship Builder

### ۱. `SceneGroupingBuilder` — اولین و ساده‌ترین

قاب‌ها و متن‌های گفتاری را بر اساس زمان، به صحنه‌ی درست نسبت می‌دهد.

```python
entities = SceneGroupingBuilder().build([
    *frame_artifacts,
    *scene_cut_artifacts,
    *transcript_artifacts,
])
```

نکته‌ی مهم درباره‌ی این کلاس: عمداً **محدود** نگه داشته شده. اولین نسخه‌ی این سازنده فقط گروه‌بندی بر اساس هم‌پوشانی زمانی انجام می‌دهد — نه چیز پیچیده‌تری مثل «فهمیدن معنای صحنه». دلیلش این بود که تیم توسعه می‌خواست اول ثابت کند که اصلِ تبدیل «Artifact به Entity» درست کار می‌کند، قبل از این‌که بلندپروازی بیشتری نشان دهد.

### ۲. `SceneSequenceBuilder` — روابط بین صحنه‌ها

```python
relationships = SceneSequenceBuilder().relate(scene_entities)
```

ورودی‌اش دیگر Artifact نیست، خودِ Entity هاست. یک Entity جدید از نوع `EntityKind.RELATIONSHIP` می‌سازد که می‌گوید «صحنه‌ی N قبل از صحنه‌ی N+1 است».

### ۳. `SceneFaceBuilder` — اولین ترکیب دو حوزه

چهره‌های تشخیص‌داده‌شده در قاب‌ها را به صحنه‌ی درست نسبت می‌دهد. نکته‌ی جالب این‌جاست: وقتی این کلاس ساخته می‌شد، تصور می‌شد که نیاز به یک نوع سازنده‌ی کاملاً جدید داریم (چون هم به Artifact نیاز داریم هم به Entity های قبلاً ساخته‌شده). اما بعد از بررسی دقیق مشخص شد که نیازی به این کار نیست — کافی بود `FaceDetectionArtifact` مسیر فایل قابِ منبع خودش را نگه دارد (`source_frame_path`)، و همین برای تطبیق با `FrameExtractionArtifact.frame_path` کافی بود.

### ۴. `SceneTextBuilder` — تأیید دوباره‌ی همان الگو

دقیقاً همان الگوی `SceneFaceBuilder` را برای متن تشخیص‌داده‌شده (OCR) تکرار می‌کند. این‌که همان الگو بدون هیچ تغییری برای یک قابلیت کاملاً متفاوت کار کرد، یک تأیید واقعی بود که این الگو تصادفی نبوده.

### ۵. `SceneMergeBuilder` — ترکیب خروجی چند سازنده

فرض کن `SceneGroupingBuilder` یک Entity برای «صحنه‌ی ۰» با دیالوگ ساخته، و `SceneFaceBuilder` یک Entity **جداگانه** برای همان «صحنه‌ی ۰» با تعداد چهره ساخته. این دو Entity الان جدا از هم هستند. `SceneMergeBuilder` این‌ها را با هم ترکیب می‌کند:

```python
merged = SceneMergeBuilder().relate([*dialogue_entities, *face_entities])
merged[0].metadata["scene_grouping"]["payload"]  # دیالوگ
merged[0].metadata["scene_face"]["total_faces"]  # تعداد چهره
```

نکته‌ی طراحی: داده‌ی هر سازنده زیر یک کلید جدا (به نام همان سازنده) نگه داشته می‌شود — نه این‌که مستقیماً با هم قاطی شوند. این‌طوری اگر یک سازنده‌ی سوم یا چهارم بعداً اضافه شود، هیچ خطر تصادفیِ رونویسی روی داده‌ی سازنده‌ی دیگر وجود ندارد.

### ۶. `FactExtractionBuilder` — اولین‌بار که یک «حقیقت» ساخته می‌شود

تا این‌جا، همه‌ی سازنده‌ها فقط Artifact های خام را *بازآرایی* می‌کردند (مثلاً «این قاب‌ها مال این صحنه‌اند»). `FactExtractionBuilder` اولین سازنده‌ای است که واقعاً یک لایه بالاتر می‌رود:

```python
fact_entities = FactExtractionBuilder().build(caption_artifacts + detection_artifacts)
fact_entities[0].kind  # EntityKind.FACT
fact_entities[0].payload  # "a cat sitting on a windowsill"
```

هر `CaptionArtifact` مستقیماً به یک `Fact` تبدیل می‌شود (متن توضیح، همان‌طور که مدل گفته). هر `ObjectDetectionArtifact` هم به یک `Fact` تبدیل می‌شود، اما این‌بار با یک قالب ساده‌ی متنی («X detected») چون تشخیص شیء، برخلاف توضیح تصویر، از اول متن ندارد.

نکته‌ی خیلی مهم درباره‌ی محدودیت عمدی‌اش: این سازنده **هیچ ادغامی انجام نمی‌دهد** — نه ادغام چند توضیح از یک قاب، نه ترکیب با متن OCR همان قاب، نه فیلتر کردن بر اساس اطمینان (confidence) فراتر از چیزی که خودِ Provider از قبل اعمال کرده. این عمداً است: دقیقاً همان انضباطی که `SceneGroupingBuilder` در روز اول داشت (به بالا نگاه کن) — اول ثابت کن یک تبدیل واقعی کار می‌کند، بعد پیچیده‌ترش کن، فقط وقتی یک نیاز واقعیِ دوم آن را لازم کرد.

نکته‌ی فنی درباره‌ی «منشأ» (Provenance): این سازنده از `Entity.provenance.source_artifact_ids` برای ردیابی استفاده می‌کند (که در فایل ۴ دیدی، حالا واقعاً هم در فایل ذخیره می‌شود)، نه از قرارداد `EvidenceAnchor`/`EvidenceLink` که در بخش بعد می‌بینی — چون یک توضیحِ کل‌تصویر، بازه یا ناحیه‌ی مشخصی در تصویر ندارد که `EvidenceAnchor` بخواهد آن را نگه دارد.

## زیرساخت شواهد (Evidence) و منشأ (Provenance) — پنج کار Phase 0

قبل از این‌که `FactExtractionBuilder` نوشته شود، یک بررسیِ پیاده‌سازی (implementation review) چهار مشکل واقعی در پایه‌ی پروژه پیدا کرد (داستان کاملش در فایل ۱). ADR-0024 برای پاسخ به آن‌ها پنج کار Phase 0 تعریف کرد: سریال‌سازی Provenance، هویت درست کش، قرارداد شواهد، جداسازی کش از رکورد ماندگار، و manifest اجرا. تغییرناپذیری عمیقِ metadata هنوز عمداً باز مانده است.

### `Provenance` حالا واقعاً ذخیره می‌شود

```python
@dataclass(frozen=True, slots=True)
class Provenance:
    builder: str
    source_artifact_ids: tuple[UUID, ...] = ()
    confidence: float | None = None
```

قبلاً، اگر یک `Entity` با یک `Provenance` واقعی را در `FileEntityStore` ذخیره می‌کردی، پایتون خطای `TypeError: Object of type Provenance is not JSON serializable` می‌داد — چون کد تبدیل به JSON نمی‌دانست این کلاس دلخواه را چطور به دیکشنری ساده تبدیل کند. الان `_serialize_value`/`entity_from_dict` (در `sceneforge/knowledge/storage.py`) این تبدیل را انجام می‌دهند، با تست‌هایی که مستقیماً همان مسیر شکست قبلی را چک می‌کنند.

### `EvidenceAnchor` و `EvidenceLink` — یک قرارداد تایپ‌شده، هنوز بدون مصرف‌کننده

```python
@dataclass(frozen=True, slots=True)
class EvidenceAnchor:
    media_id: UUID
    stream: str | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    spatial_region: tuple[float, float, float, float] | None = None
    asset_ref: str | None = None
    edition_id: str | None = None
    id: UUID = field(default_factory=uuid4)
```

این یعنی «دقیقاً کدام بخش از کدام رسانه، این ادعا را پشتیبانی می‌کند» — مثلاً «ثانیه‌ی ۳.۵ تا ۴.۰ از این ویدیو» یا «این ناحیه‌ی مستطیلی از این تصویر». `EvidenceLink` هم دو `Reference` (نوع + شناسه) را با یک رابطه‌ی مشخص (`supports` یا `derived_from`) به هم وصل می‌کند. نکته‌ی صادقانه: **تا امروز هیچ سازنده‌ای این دو نوع را تولید نمی‌کند** — چون `Entity.parents` برای نیازهای فعلی کافی بوده. زیرساختش آماده و تست‌شده است، اما طبق همان اصل «قبل از رسمی‌کردن، اثبات کن»، فقط وقتی یک Fact/Event Builder واقعاً به دقتِ «کدام بازه‌ی دقیق» نیاز داشته باشد، استفاده می‌شود.

### `AnalysisRun` — یک بیانیه‌ی «دقیقاً چه چیزی اجرا شد»

وقتی یک `Pipeline` را با آرگومان اختیاری `analysis_run=` اجرا کنی، برای هر مرحله یک `StageRecord` ساخته می‌شود: outcome یکی از `ATTEMPTED`/`SKIPPED`/`FAILED` است و `cache_hit` جداگانه می‌گوید پاسخِ مرحله‌ی `ATTEMPTED` تازه اجرا شده یا از cache آمده؛ نسخه‌ی Provider هم ثبت می‌شود. این برای batchهای بزرگ مفید است. **هنوز ماندگار (persistent) نیست** — چون هنوز هیچ session واقعی چند-Providerی وجود ندارد که به ذخیره‌ی آن نیاز داشته باشد.

### `KnowledgeRecordStore` — جدا کردن «کش» از «رکورد ماندگار»

```python
record_store = FileKnowledgeRecordStore("./records")
record_store.append("scene:0", [some_entity])  # نسخه‌ی شماره‌دارِ جدید
record_store.retract("scene:0", reason="اطلاعات جدید نشان داد اشتباه بود")
```

قبل از این، `EntityStore` هم‌زمان دو نقش داشت: هم یک کشِ قابل‌حذف (اگر Provider عوض شود، نتیجه‌ی قدیمی بی‌فایده می‌شود و می‌توان رویش نوشت)، هم — به‌طور ضمنی — یک رکورد دانشیِ ماندگار. این دو مفهوم فرق دارند: یک نتیجه‌ی کش را می‌توان بی‌دغدغه پاک کرد (چون دوباره قابل‌محاسبه است)، اما یک نتیجه‌ی دانشی («ما این را باور داشتیم») نباید بی‌سروصدا ناپدید شود. `KnowledgeRecordStore` هیچ متد `put`/`delete` ندارد — فقط `append()` (نسخه‌ی جدید) و `retract()` (ثبتِ رسمیِ «دیگر این را باور نداریم»، نه پاک‌کردن نسخه‌ی قبلی).

### محدودیت حل‌نشده: تغییرناپذیری عمیق

`MappingProxyType` فقط mapping بیرونیِ `Artifact.metadata`/`Entity.metadata` را محافظت می‌کند. اگر مقدار یکی از کلیدها یک `list` یا `dict` باشد، محتوای آن هنوز می‌تواند درجا تغییر کند. جداسازی `KnowledgeRecordStore` از cache این را حل نمی‌کند؛ ADR-0024 آن را صریحاً برای طراحی یک payload تایپ‌شده و واقعاً frozen در آینده باز گذاشته است.

## EntityStore — کش فایل‌محور یا درون‌حافظه‌ای برای Entity ها

```python
store = FileEntityStore("./cache")
entities = build_with_cache(SceneGroupingBuilder(), artifacts, store)
```

دقیقاً مثل `FileArtifactStore` برای Artifact ها، اما با یک تفاوت مهم در نحوه‌ی ساخت کلید کش: چون یک سازنده‌ی دانش می‌تواند از **چند فیلم مختلف در یک فراخوانی** استفاده کند (نه فقط یک `Media`)، کلید کش برای Entity بر اساس «مجموعه‌ی دقیق شناسه‌های Artifact ورودی + نام و نسخه‌ی سازنده» ساخته می‌شود، نه بر اساس یک `Media` خاص. این Store قابل‌رونویسی/حذف است و نقش cache دارد؛ برای تاریخچه‌ی ماندگار باید از `KnowledgeRecordStore` بالا استفاده شود.

## پرسیدن سؤال از دانش ذخیره‌شده

```python
from sceneforge.knowledge import iter_all_entities, find_related

# همه‌ی چیزهایی که در کل حافظه ذخیره شده
for entity in iter_all_entities(store):
    ...

# همه‌چیزی که به یک Entity خاص مرتبط است
related = find_related(store, some_entity_id)
```

نکته‌ی جالب: تا امروز، **هیچ ایندکس یا پایگاه‌داده‌ی گرافی وجود ندارد.** این دو تابع فقط همه‌چیز را می‌خوانند و در پایتون فیلتر می‌کنند. این ساده به‌نظر می‌رسد، اما چهار بار جداگانه با آزمایش واقعی ثابت شده که کافی است:

- جست‌وجوی هدفمند در ۱۱٬۷۰۰ Entity: **۰.۱۲۵ ثانیه**
- تجمیع کامل روی کل کتابخانه (۴۰۰ فیلم، ۲۳٬۶۰۰ Entity): **۰.۳۹۱ ثانیه**

## اولین برنامه‌ی واقعی: `SceneSummary`

```python
from sceneforge.applications.scene_summary import SceneSummary

summary = SceneSummary(store)
data, markdown = summary.generate()  # یا فقط summary.render_markdown()
print(markdown)  # خروجی: یک متن Markdown با خلاصه‌ی هر صحنه
```

این اولین «برنامه» (Application) واقعی پروژه است — یعنی اولین چیزی که Entity های ذخیره‌شده را می‌خواند و یک خروجیِ واقعاً قابل‌استفاده برای انسان می‌سازد. تا قبل از این، همه‌چیز فقط زیرساخت بود؛ این برنامه اولین‌بار است که وعده‌ی چشم‌انداز پروژه (فایل ۱) واقعاً نشان داده می‌شود.

### چطور یک Fact به صحنه‌اش وصل می‌شود، بدون یک Builder جدید

بعد از این‌که `FactExtractionBuilder` واقعی شد، یک محدودیت باقی ماند: `SceneSummary` هر Fact را در یک لیست جدا و مسطح نشان می‌داد، بدون هیچ ارتباطی به صحنه‌ای که در آن دیده شده — چون `Fact.metadata["media_id"]` مالِ همان تصویر/قابی است که از آن توضیح گرفته شده، نه مالِ ویدیوی اصلی؛ یعنی نمی‌شد این دو را با `media_id` به هم وصل کرد (دقیقاً همان مشکلی که در فایل ۵، قدم ۷ درباره‌ی تشخیص چهره دیدی).

راه‌حل، یک Builder جدید نبود. `SceneSummary.collect()` همان الگوی شناخته‌شده‌ی `source_frame_path` (که `SceneFaceBuilder`/`SceneTextBuilder` از قبل استفاده می‌کردند) را در لایه‌ی خودِ برنامه به‌کار برد:

```python
frame_path_to_scene_id: dict[str, UUID] = {}
scene_index_by_id: dict[UUID, int] = {}
for scene_entity in scene_entities:
    scene_index_by_id[scene_entity.id] = scene_entity.metadata["scene_index"]
    for frame_path in scene_entity.metadata.get("frame_paths", []):
        frame_path_to_scene_id[frame_path] = scene_entity.id

for fact_entity in fact_entities:
    source_frame_path = fact_entity.metadata.get("source_frame_path")
    scene_id = frame_path_to_scene_id.get(source_frame_path)
    scene_index = scene_index_by_id.get(scene_id)
    # اگر پیدا شد → این Fact زیر همان صحنه نمایش داده می‌شود
    # اگر پیدا نشد → همچنان در لیست مسطحِ «Facts» می‌ماند، نه این‌که گم شود
```

چرا این یک Builder یا Protocol جدید نشد؟ چون هیچ نیازی نبود که این ارتباط یک `Entity` ماندگار و قابل‌جست‌وجو باشد — فقط یک برنامه‌ی واحد (`SceneSummary`) به آن نیاز داشت، در لحظه‌ی نمایش. اگر روزی یک مصرف‌کننده‌ی دوم به همین ارتباط نیاز پیدا کند (مثلاً یک برنامه‌ی دیگر که می‌خواهد بپرسد «همه‌ی Fact های صحنه‌ی ۳ کدام‌اند؟»)، طبق همان اصل «قبل از رسمی‌کردن، اثبات کن»، آن‌وقت وقتش است که به یک `RelationshipBuilder` واقعی تبدیل شود — نه زودتر.

## چشم‌انداز «مدل جهان» — کدام بخش‌هایش واقعی شدند؟

یک سند بلند و بلندپروازانه پیشنهاد داد که SceneForge باید فیلم را «مثل انسان‌ها به‌خاطر می‌سپارند» مدل کند — با نُه لایه از شواهد تا درون‌مایه، و یک شیء مرکزی به‌نام `WorldModel`. هنگام ADR-0021، دو بخش از این ایده به ساختار موجود نگاشت شدند: `Entity.provenance` و Artifact/Entityهای frozen با `parents`. بررسی بعدی در ADR-0024 نشان داد این پایه کامل نیست: Provenance ذخیره نمی‌شد، Storeهای cache حذف‌پذیر بودند، و metadata تودرتو عمیقاً frozen نبود. بقیه‌ی لایه‌ها هم آن زمان منبع داده‌ی واقعی نداشتند — چون هیچ Provideری چیزی بالاتر از تشخیص خام تولید نمی‌کرد.

تصمیم نهایی (در [`docs/adr/0021-world-model-vocabulary.md`](../adr/0021-world-model-vocabulary.md)): این چشم‌انداز به‌عنوان **واژگان و جهت‌گیری** پذیرفته شد (در `docs/architecture/DOMAIN_MODEL.md` مستند شده)، اما هیچ‌کدام از لایه‌های بالاتر ساخته نشدند تا وقتی که یک Provider واقعی داده‌ی واقعی برایشان تولید کند.

**وضعیت امروز، صادقانه:** لایه‌ی «حقایق» (Facts) دیگر فقط واژگان نیست — واقعی شده (بخش‌های بالای همین فایل). یک بررسیِ بعدیِ پیاده‌سازی (`ADR-0024`) هم چهار مشکلِ واقعیِ زیرساختی پیدا کرد؛ Phase 0 هویت کش، ذخیره‌ی Provenance، قرارداد شواهد، جداسازی کش از رکورد ماندگار، و manifest اجرا را تحویل داد، اما تغییرناپذیری عمیقِ metadata هنوز حل نشده است. لایه‌های بالاتر از Facts (رویدادها، وضعیت، نیت‌ها، روایت، درون‌مایه) هنوز هیچ تولیدکننده‌ی واقعی ندارند — پس هنوز عمداً ساخته نشده‌اند.

---

مرحله‌ی بعد: [`08-how-to-extend.md`](08-how-to-extend.md) — اگر می‌خواهی خودت یک Provider یا Builder جدید اضافه کنی.
