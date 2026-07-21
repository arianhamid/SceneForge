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
names: list[str]              # لیستی از رشته‌ها
mapping: dict[str, int]       # دیکشنری با کلید رشته و مقدار عدد
maybe_name: str | None        # یا رشته است، یا None (یعنی «هیچ‌چیز»)
pair: tuple[int, int]         # یک زوج ثابت از دو عدد
```

`str | None` را خیلی زیاد می‌بینی — یعنی «این مقدار یا از نوع X است، یا اصلاً وجود ندارد (`None`)». مثلاً در کد واقعی پروژه:

```python
source = media.metadata.get("source")   # این می‌تواند str یا None باشد
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
print(artifact.frame_path)   # /tmp/frame.png
print(artifact.media_id)     # یک UUID تصادفی جدید
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

---

با این پس‌زمینه، حالا آماده‌ای بروی سراغ [`04-core-concepts.md`](04-core-concepts.md) و ببینی این مفاهیم چطور کنار هم، مفاهیم اصلی پروژه را می‌سازند.
