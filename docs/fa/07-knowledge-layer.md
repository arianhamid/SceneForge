# ۷. لایه‌ی دانش — از Artifact تا فهمیدن

## Entity چیست؟

`Entity` معادل `Artifact` در لایه‌ی دانش است — اما با یک فرق مهم: `Artifact` نتیجه‌ی *یک* Provider است، `Entity` نتیجه‌ی *ترکیب چند* Artifact (احتمالاً از چند Provider مختلف) است.

```python
@dataclass(frozen=True, slots=True)
class Entity(Generic[T]):
    id: UUID = field(default_factory=uuid4)
    kind: EntityKind = EntityKind.ENTITY
    builder: str = "unknown"
    payload: T = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    parents: tuple[UUID, ...] = ()
```

خیلی شبیه `Artifact` است، عمداً — همان انضباط غیرقابل‌تغییری، همان `parents` برای ردیابی منشأ.

## پنج سازنده‌ی دانش (Knowledge Builder) واقعی

### ۱. `SceneGroupingBuilder` — اولین و ساده‌ترین

قاب‌ها و متن‌های گفتاری را بر اساس زمان، به صحنه‌ی درست نسبت می‌دهد.

```python
entities = SceneGroupingBuilder().build([*frame_artifacts, *scene_cut_artifacts, *transcript_artifacts])
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
merged[0].metadata["scene_grouping"]["payload"]   # دیالوگ
merged[0].metadata["scene_face"]["total_faces"]   # تعداد چهره
```

نکته‌ی طراحی: داده‌ی هر سازنده زیر یک کلید جدا (به نام همان سازنده) نگه داشته می‌شود — نه این‌که مستقیماً با هم قاطی شوند. این‌طوری اگر یک سازنده‌ی سوم یا چهارم بعداً اضافه شود، هیچ خطر تصادفیِ رونویسی روی داده‌ی سازنده‌ی دیگر وجود ندارد.

## EntityStore — حافظه‌ی دائمی برای Entity ها

```python
store = FileEntityStore("./cache")
entities = build_with_cache(SceneGroupingBuilder(), artifacts, store)
```

دقیقاً مثل `FileArtifactStore` برای Artifact ها، اما با یک تفاوت مهم در نحوه‌ی ساخت کلید کش: چون یک سازنده‌ی دانش می‌تواند از **چند فیلم مختلف در یک فراخوانی** استفاده کند (نه فقط یک `Media`)، کلید کش برای Entity بر اساس «مجموعه‌ی دقیق شناسه‌های Artifact ورودی + نام سازنده» ساخته می‌شود، نه بر اساس یک `Media` خاص.

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

summary = SceneSummary(store).build()
print(summary)  # خروجی: یک متن Markdown با خلاصه‌ی هر صحنه
```

این اولین «برنامه» (Application) واقعی پروژه است — یعنی اولین چیزی که Entity های ذخیره‌شده را می‌خواند و یک خروجیِ واقعاً قابل‌استفاده برای انسان می‌سازد. تا قبل از این، همه‌چیز فقط زیرساخت بود؛ این برنامه اولین‌بار است که وعده‌ی چشم‌انداز پروژه (فایل ۱) واقعاً نشان داده می‌شود.

## چشم‌انداز «مدل جهان» و این‌که چرا هنوز ساخته نشده

یک سند بلند و بلندپروازانه پیشنهاد داد که SceneForge باید فیلم را «مثل انسان‌ها به‌خاطر می‌سپارند» مدل کند — با نُه لایه از شواهد تا درون‌مایه، و یک شیء مرکزی به‌نام `WorldModel`. تیم توسعه این ایده را بررسی کرد و دو نتیجه گرفت:

1. دو ایده‌ی این سند از قبل، به‌طور مستقل، واقعی شده بودند: `Entity.provenance` (این‌که هر Entity بداند «چرا این را باور دارم») و «شواهد هرگز حذف نمی‌شود» (که از قبل به‌طور ساختاری درست بود چون همه‌چیز غیرقابل‌تغییر است).
2. بقیه‌ی لایه‌ها (حقایق، رویدادها، وضعیت، نیت‌ها، روایت، درون‌مایه) **هیچ منبع داده‌ی واقعی‌ای ندارند** — چون هیچ Provideری هنوز چیزی بالاتر از تشخیص خام تولید نمی‌کند.

تصمیم نهایی (در [`docs/adr/0021-world-model-vocabulary.md`](../adr/0021-world-model-vocabulary.md)): این چشم‌انداز به‌عنوان **واژگان و جهت‌گیری** پذیرفته شد (در `docs/architecture/DOMAIN_MODEL.md` مستند شده)، اما هیچ‌کدام از لایه‌های بالاتر ساخته نشدند تا وقتی که یک Provider واقعی (مثل تشخیص شیء یا توضیح تصویر) داده‌ی واقعی برایشان تولید کند.

---

مرحله‌ی بعد: [`08-how-to-extend.md`](08-how-to-extend.md) — اگر می‌خواهی خودت یک Provider یا Builder جدید اضافه کنی.
