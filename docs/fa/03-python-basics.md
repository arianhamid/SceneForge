# ۳. مفاهیم پایتونی استفاده‌شده در پروژه

این فایل برای کسی نوشته شده که پایتون را کامل بلد نیست اما می‌خواهد کدهای SceneForge را بفهمد. تمام مثال‌ها دقیقاً از سبک واقعی کد پروژه گرفته شده‌اند، نه مثال‌های انتزاعی.

## ۱. Type Hints (راهنمای نوع)

در پایتون معمولی، نوع متغیرها را مشخص نمی‌کنی. اما در SceneForge، همه‌جا نوع مشخص شده — این کار خطاها را قبل از اجرا نشان می‌دهد (با ابزاری به‌نام `mypy`).

```python
def add(a: int, b: int) -> int:
    return a + b
```

اینجا `a: int` یعنی «a باید عدد صحیح باشد»، و `-> int` یعنی «خروجی تابع عدد صحیح است».

نوع‌های پیچیده‌تر که زیاد می‌بینی:

```python
names: list[str]  # لیستی از رشته‌ها
mapping: dict[str, int]  # دیکشنری با کلید رشته و مقدار عدد
maybe_name: str | None  # یا رشته است، یا None (یعنی «هیچ‌چیز»)
pair: tuple[int, int]  # یک زوج ثابت از دو عدد
```

`str | None` را خیلی زیاد می‌بینی — یعنی «این مقدار یا از نوع X است، یا اصلاً وجود ندارد (`None`)». مثلاً در کد واقعی پروژه:

```python
source = media.metadata.get("source")  # این می‌تواند str یا None باشد
if not source:
    raise ProviderError("...")
```

## ۲. Dataclass — کلاس‌های داده

اکثر کلاس‌های پروژه (`Media`، `Artifact`، `Entity`) با `@dataclass` نوشته شده‌اند. این یک دکوراتور (decorator) است که خودکار متد `__init__` و مقایسه (`==`) می‌سازد، تا لازم نباشد دستی بنویسی.

```python
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class FrameExtractionArtifact:
    media_id: UUID = field(default_factory=uuid4)
    frame_path: str = ""
    timestamp_seconds: float = 0.0
```

نکات مهم:

- **`frozen=True`** یعنی بعد از ساختن یک نمونه، نمی‌توانی مقادیرش را تغییر دهی. اگر بنویسی `artifact.frame_path = "x"`، خطا می‌گیری. این عمداً است — کل پروژه بر پایه‌ی «چیزی که ساخته شد هرگز تغییر نمی‌کند» بنا شده (به فایل ۱، اصل شماره ۴ نگاه کن).
- **`slots=True`** یک بهینه‌سازی حافظه است؛ فعلاً لازم نیست نگرانش باشی.
- **`field(default_factory=uuid4)`** یعنی «هر بار که یک نمونه‌ی جدید بدون مقدار صریح برای این فیلد بسازی، تابع `uuid4()` صدا زده می‌شود تا یک شناسه‌ی یکتای جدید بسازد». اگر به‌جایش می‌نوشتیم `media_id: UUID = uuid4()`، همه‌ی نمونه‌ها یک شناسه‌ی مشترک می‌گرفتند (یک باگ رایج پایتون).

برای ساختن یک نمونه:

```python
artifact = FrameExtractionArtifact(frame_path="/tmp/frame.png", timestamp_seconds=1.5)
print(artifact.frame_path)  # /tmp/frame.png
print(artifact.media_id)  # یک UUID تصادفی جدید
```

### چطور یک dataclass غیرقابل‌تغییر را «تغییر» بدهیم؟

چون `frozen=True` اجازه‌ی تغییر مستقیم نمی‌دهد، برای «اصلاح» یک مقدار، یک **نسخه‌ی جدید** می‌سازیم:

```python
from dataclasses import replace

new_artifact = replace(artifact, timestamp_seconds=2.0)
# artifact اصلی دست‌نخورده می‌ماند؛ new_artifact یک شیء کاملاً جدید است
```

در کلاس `Media`، این کار با یک متد کمکی به‌نام `evolve()` انجام می‌شود که همین کار را می‌کند اما مقادیر `metadata` را هم با هم ادغام می‌کند (به‌جای جایگزینی کامل).

## ۳. Enum و StrEnum — لیست ثابت از گزینه‌ها

وقتی می‌خواهیم بگوییم «این مقدار فقط می‌تواند یکی از چند گزینه‌ی مشخص باشد» (نه هر رشته‌ی دلخواه)، از `Enum` استفاده می‌کنیم. این از اشتباه تایپی جلوگیری می‌کند.

```python
from enum import StrEnum


class ArtifactKind(StrEnum):
    FRAME = "frame"
    TRANSCRIPT = "transcript"
    OCR = "ocr"
```

حالا به‌جای این‌که در کد بنویسی `kind="frmae"` (با غلط تایپی) که هیچ خطایی نمی‌دهد، می‌نویسی `kind=ArtifactKind.FRAME` که اگر اشتباه تایپ کنی، پایتون فوراً خطا می‌دهد.

## ۴. Protocol در برابر ABC — دو راه برای تعریف «قرارداد»

پروژه از دو روش برای گفتن «این کلاس باید این متدها را داشته باشد» استفاده می‌کند.

### ABC (Abstract Base Class) — وراثت اجباری

```python
from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def run(self, media): ...
```

هر کلاسی که بخواهد `Provider` باشد، باید صریحاً از آن ارث‌بری کند: `class MyProvider(Provider): ...`

### Protocol — قرارداد ساختاری (بدون نیاز به وراثت)

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class KnowledgeBuilder(Protocol):
    @property
    def name(self) -> str: ...
    def build(self, artifacts): ...
```

هر کلاسی که *به‌طور طبیعی* متدهای `name` و `build` را داشته باشد، «یک KnowledgeBuilder محسوب می‌شود» — حتی اگر هیچ‌وقت صریحاً از `KnowledgeBuilder` ارث‌بری نکرده باشد. این شبیه به این است که بگوییم «اگر مثل اردک راه برود و مثل اردک صدا کند، اردک است» — نه این‌که حتماً باید گواهی «من اردک هستم» داشته باشد.

پروژه معمولاً از `Protocol` استفاده می‌کند وقتی می‌خواهد افزونه‌ها (Plugin) بتوانند بدون وابستگی مستقیم به کد هسته، پیاده‌سازی کنند.

## ۵. Generic — کلاس‌هایی که با هر نوعی کار می‌کنند

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Artifact(Generic[T]):
    payload: T
```

اینجا `T` یک «نوع جایگزین‌شدنی» است. وقتی می‌نویسیم `Artifact[str]`، یعنی `payload` این Artifact حتماً از نوع `str` است. وقتی می‌نویسیم `Artifact[None]`، یعنی این Artifact اصلاً `payload` معناداری ندارد (مثل `FrameExtractionArtifact` که فقط مسیر فایل را دارد، نه یک محتوای اصلی).

## ۶. property — متدی که مثل یک فیلد رفتار می‌کند

```python
class Pipeline:
    @property
    def provider(self):
        return self._provider
```

با `@property`، می‌توانی بنویسی `pipeline.provider` (بدون پرانتز) به‌جای `pipeline.provider()`. این برای خواندن مقادیر «فقط-خواندنی» به شکل تمیزتر استفاده می‌شود.

## ۷. Exception های سفارشی — چرا فقط `Exception` استفاده نمی‌شود؟

در پایتون معمولی می‌توانی بنویسی `raise Exception("خطا شد")`. اما در SceneForge، همیشه یک کلاس اختصاصی داریم:

```python
class SceneForgeError(Exception):
    """پایه‌ی همه‌ی خطاهای پروژه."""


class ProviderError(SceneForgeError):
    """وقتی یک Provider نتواند کارش را انجام دهد."""
```

فایده‌اش: کسی که از پروژه استفاده می‌کند می‌تواند بنویسد `except ProviderError:` و فقط خطاهای مربوط به Provider را بگیرد، بدون این‌که خطاهای دیگر (مثلاً خطای برنامه‌نویسی) را قورت بدهد.

### الگوی `raise ... from exc`

```python
try:
    result = some_risky_call()
except Exception as exc:
    raise ProviderError(f"شکست خورد: {exc}") from exc
```

این یعنی: «این خطای جدید را پرتاب کن، اما ردپای خطای اصلی (traceback) را هم نگه دار». اگر `from exc` را حذف کنی، وقتی خطا رخ دهد نمی‌فهمی علت اصلی‌اش چه بوده.

## ۸. async / await — برای کارهای کند و هم‌زمان

بخشی از پروژه (`AsyncPipeline`) از `async`/`await` استفاده می‌کند — برای وقتی که چند Provider کند (مثل تماس با یک مدل) باید هم‌زمان اجرا شوند، بدون این‌که منتظر تمام‌شدن یکی‌یکی بمانیم.

```python
async def run(self, media):
    result = await self._provider.run(media)
    return result
```

`async def` یعنی «این تابع می‌تواند در وسط اجرا، اجازه بدهد کارهای دیگر هم پیش بروند». `await` یعنی «اینجا صبر کن تا این کار کند تمام شود، اما در حین صبر، بقیه‌ی برنامه بلوکه نشود».

اگر فعلاً `async`/`await` گیج‌کننده است، مشکلی نیست — بیشتر کدهای پروژه (نسخه‌ی معمولی و هم‌زمانِ `Pipeline`) بدون `async` کار می‌کنند و برای شروع کافی است همان را بفهمی.

## ۹. `with` — مدیریت خودکار منابع

کد پروژه در تست‌ها زیاد از `with pytest.raises(...)` استفاده می‌کند:

```python
with pytest.raises(ProviderError):
    provider.run(bad_media)
```

یعنی: «انتظار دارم کد داخل این بلوک، دقیقاً همین خطا را بدهد؛ اگر نداد، خودِ تست شکست بخورد».

## ۱۰. `defaultdict` — دیکشنری که هرگز `KeyError` نمی‌دهد

در کد پروژه (مثلاً `sceneforge/knowledge/scene_grouping_builder.py` و `sceneforge/applications/scene_summary.py`) خیلی زیاد این الگو را می‌بینی: می‌خواهیم چند چیز را بر اساس یک کلید دسته‌بندی کنیم.

```python
from collections import defaultdict
from uuid import UUID

facts_by_scene_id: dict[UUID, list[FactData]] = defaultdict(list)
for scene_id, fact in correlated_facts:
    facts_by_scene_id[scene_id].append(fact)
```

با یک `dict` معمولی، خط دوم باید این‌طور می‌بود:

```python
if scene_id not in facts_by_scene_id:
    facts_by_scene_id[scene_id] = []
facts_by_scene_id[scene_id].append(fact)
```

`defaultdict(list)` یعنی «هر بار که به یک کلیدِ ناموجود دسترسی پیدا کنی، به‌جای خطا، یک لیستِ خالیِ جدید بساز و همان را برگردان». همین یک خط، آن سه خط شرطی را حذف می‌کند.

## ۱۱. `pathlib` — کار با مسیر فایل، به‌جای رشته‌ی خام

پروژه تقریباً هیچ‌جا مسیر فایل را به‌شکل رشته‌ی خام دست‌کاری نمی‌کند (مثلاً با `+` یا `os.path.join`)؛ همیشه از `pathlib.Path` استفاده می‌کند:

```python
from pathlib import Path

output_dir = Path(cache_dir) / "frames"
output_dir.mkdir(parents=True, exist_ok=True)
frame_path = output_dir / f"{media.id}_frame_{index:04d}.png"
```

فایده‌اش: `/` بین دو `Path` به‌طور خودکار جداکننده‌ی درست سیستم‌عامل را می‌گذارد (روی ویندوز `\`، روی لینوکس/مک `/`) — دیگر لازم نیست خودت نگران این تفاوت باشی. `output_dir.is_file()`، `output_dir.exists()`، و مشابه آن هم خواناتر از توابع جداگانه‌ی ماژول `os.path` هستند.

## ۱۲. الگوهای تست‌نویسی با `pytest`

چون این پروژه به‌شدت روی تست تکیه دارد (نزدیک به ۵۰۰ تست)، فهمیدن چند الگوی تکرارشونده در `tests/` کمک زیادی می‌کند.

### Fixture — آماده‌سازی مشترک بین چند تست

```python
import pytest
from pathlib import Path


@pytest.fixture
def video_with_two_scenes(tmp_path: Path) -> Path:
    path = tmp_path / "two_scenes.mp4"
    # ... اینجا با ffmpeg واقعی یک ویدیوی واقعی ساخته می‌شود
    return path


def test_scene_detection_finds_two_scenes(video_with_two_scenes):
    # pytest به‌طور خودکار video_with_two_scenes را می‌سازد و اینجا تزریق می‌کند
    ...
```

`tmp_path` خودش یک fixture آماده‌ی خودِ pytest است — یک پوشه‌ی موقتِ تازه برای هر تست، که بعد از تمام‌شدن تست خودکار پاک می‌شود.

### `pytest.importorskip` و `pytest.mark.skipif` — رد شدن صادقانه از کنار وابستگی‌های نصب‌نشده

```python
pytest.importorskip(
    "cv2"
)  # اگر opencv نصب نیست، این تست را «رد شده» علامت بزن، نه «شکست‌خورده»

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
pytestmark = pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="ffmpeg/ffprobe not on PATH"
)
```

فرق مهم: یک تستِ **رد‌شده (skipped)** یعنی «این محیط نمی‌تواند این را چک کند»، اما یک تستِ **شکست‌خورده (failed)** یعنی «چیزی واقعاً خراب است». قاطی‌کردن این دو، اعتماد به کل مجموعه‌ی تست را از بین می‌برد — چون دیگر نمی‌دانی وقتی یک تست قرمز می‌شود، واقعاً یک باگ است یا فقط یک پکیج نصب نیست.

### `pytest.raises` — انتظار داشتن یک خطای مشخص

قبلاً در بخش ۹ دیدی؛ نکته‌ی تکمیلی: همیشه دقیق‌ترین کلاس خطا را چک کن (مثلاً `ProviderError`، نه `Exception` عمومی) — وگرنه تست می‌تواند حتی وقتی کد یک باگ کاملاً نامرتبط دارد، باز هم «سبز» بماند.

## ۱۳. خلاصه: چند بهترین‌شیوه (Best Practice) که در سراسر این پروژه دیده می‌شود

این‌ها قانون‌های نانوشته‌ای هستند که با خواندن کد واقعی پروژه می‌شود استخراجشان کرد — و اگر می‌خواهی به این پروژه کد اضافه کنی، رعایتشان انتظار می‌رود:

1. **هیچ‌وقت `except Exception` بدون دلیل صریح استفاده نکن.** اگر مجبوری (مثلاً برای پیچیدن خطای یک کتابخانه‌ی بیرونی در `ProviderError`)، همیشه یک کامنت `# noqa: BLE001` بگذار که بگوید «این عمدی است، یک خطای دیگر پرتاب می‌شود، قورت داده نمی‌شود» — دقیقاً همان الگویی که در فایل ۶ دیدی.
2. **مقدار پیش‌فرضِ قابل‌تغییر (mutable default argument) هرگز مستقیم استفاده نمی‌شود.** `def f(items: list = [])` یک باگ کلاسیک پایتون است — همه‌ی فراخوانی‌ها همان یک لیست را به اشتراک می‌گذارند. به‌جایش همیشه `field(default_factory=list)` (در dataclass) یا `items: list | None = None` و ساختن لیست داخل تابع.
3. **نوع دقیق‌تر همیشه بهتر از `Any` است.** `mypy --strict` روی کل پکیج `sceneforge` اجرا می‌شود؛ استفاده از `Any` جایی که یک نوع دقیق‌تر (مثل `Protocol` یا `TypeVar`) ممکن است، معمولاً در بازبینی کد رد می‌شود.
4. **تست‌ها واقعی هستند، نه فقط شبیه‌سازی‌شده — هرجا امکانش هست.** همان‌طور که در فایل ۱ دیدی، این پروژه ترجیح می‌دهد یک تست با `ffmpeg` واقعی، یک فایل واقعی، و یک ادعای اندازه‌گیری‌شده‌ی واقعی داشته باشد، تا یک mock که فقط ادعا می‌کند رفتار واقعی را شبیه‌سازی کرده.
5. **مستندسازی همیشه صادقانه است، حتی درباره‌ی محدودیت‌ها.** docstring های پروژه پر است از جملاتی مثل «هنوز تأیید نشده» یا «عمداً محدود» — به‌جای وانمود کردن که چیزی کامل‌تر از آن‌چیزی است که واقعاً هست.

---

با این پس‌زمینه، حالا آماده‌ای بروی سراغ [`04-core-concepts.md`](04-core-concepts.md) و ببینی این مفاهیم چطور کنار هم، مفاهیم اصلی پروژه را می‌سازند.
