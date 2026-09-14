# Shaparak Pro – بسته‌بندی برداری / vector packaging artwork

بازسازی برداری طرح بسته‌بندی «حوله یکبار مصرف بهداشتی Shaparak Pro» در دو نسخه‌ی
فیروزه‌ای و سرمه‌ای، رو و پشت بسته. همه‌ی عناصر (پروانه، آیکون‌ها، بارکد، QR، متن‌ها)
برداری هستند و در ایلاستریتور قابل ویرایش‌اند؛ هیچ تصویر رستری در فایل‌ها نیست.

A vector rebuild of the Shaparak Pro disposable-towel pouch in the two requested
colour ways, front and back. Everything – butterfly, icons, barcode, QR code and
type – is vector and editable in Illustrator; no raster images are embedded.

---

## کدام فایل را باز کنم؟ / Which file do I open?

| مسیر / path | چیست / what it is |
| --- | --- |
| `output/ai/*.ai` | فایل‌های PDF-compatible که ایلاستریتور مستقیم باز می‌کند (متن‌ها outline شده) |
| `output/svg-outlined/*.svg` | همان طرح‌ها به صورت SVG، متن تبدیل به منحنی – مطمئن‌ترین گزینه برای چاپ |
| `output/svg-live-text/*.svg` | نسخه‌ی متن زنده و قابل تایپ مجدد (نیاز به فونت‌های پوشه‌ی `fonts/`) |
| `output/pdf/*.pdf` | همان محتوای `.ai`، برای پیش‌نمایش و ارسال به چاپخانه |
| `output/preview/*.png` | پیش‌نمایش PNG |
| `output/shaparak-pro-presentation-sheet.svg` | شیت ارائه، مشابه چیدمان تصویر اولیه (۲ نسخه × رو و پشت) |
| `output/shaparak-pro-logo.svg` | لوگوی پروانه + لوگوتایپ به صورت جدا |

`.ai` files here are PDF-format Illustrator files: Illustrator opens them
directly and every object stays editable. If your Illustrator is older than CS6
or refuses the extension, open the matching `output/pdf/*.pdf` or drag in the
SVG instead – the content is identical.

### متن فارسی و ایلاستریتور / Persian text in Illustrator

* فایل‌های `svg-outlined` و `ai` متن را به صورت **منحنی (outline)** دارند، پس در هر
  نسخه‌ای از ایلاستریتور و روی هر سیستمی دقیقاً یکسان نمایش داده می‌شوند. برای چاپ
  همین‌ها را بفرستید.
* فایل‌های `svg-live-text` متن را زنده نگه می‌دارند. برای ویرایش فارسی/عربی به
  ایلاستریتور نسخه‌ی Middle Eastern (یا فعال‌کردن
  `Type ▸ Middle Eastern & South Asian Single Line Composer`) نیاز دارید، وگرنه
  حروف جدا و برعکس دیده می‌شوند. فونت‌های لازم در پوشه‌ی `fonts/` هستند.

## ساختار لایه‌ها / Layer structure

هر پنل با گروه‌های نام‌گذاری‌شده ساخته شده که ایلاستریتور آن‌ها را به صورت لایه
نشان می‌دهد:

```
01-BACKGROUND          زمینه و موج رنگی
02-TOP-SEAL            دوخت بالا با بافت شیاردار
03-BOTTOM-SEAL         دوخت پایین
04-HANG-SLOT           جای آویز (euro slot)
05-VISCOSE-BADGE       نشان ۱۰۰٪ ویسکوز
06-LOGO-AND-TITLES     پروانه، SHAPARAK، PRO و عناوین سه‌زبانه
07-TOWEL-BUTTERFLY     حوله‌ی تاشده به شکل پروانه
08-EXTRA-SOFT-CLAIM    ادعای EXTRA SOFT / NATURAL FIBER
09-USAGE-STRIP         نوار کاربردها
10-SIZE-OPTIONS        جدول سایزها
ZZ-MOCKUP-SHADING      سایه/براقی فیلم – فقط در شیت ارائه
ZZ-GUIDES-do-not-print راهنمای برش، ناحیه‌ی امن و بلید (مخفی)
```

لایه‌ی `ZZ-GUIDES-do-not-print` به صورت پیش‌فرض مخفی است: کادر بنفش = خط برش،
آبی = ناحیه‌ی امن (۶ میلی‌متر)، نارنجی = بلید پیشنهادی (۳ میلی‌متر). پیش از چاپ آن را
حذف کنید.

## مشخصات فنی / Specs

* اندازه‌ی هر پنل: **۱۵۰ × ۱۷۰ میلی‌متر** (واحد فایل‌ها میلی‌متر است، مقیاس ۱:۱)
* بلید پیشنهادی ۳ میلی‌متر، ناحیه‌ی امن ۶ میلی‌متر
* رنگ‌ها RGB هستند؛ پیش از چاپ به CMYK یا اسپات تبدیل کنید:

| نقش | HEX | معادل پیشنهادی چاپ |
| --- | --- | --- |
| فیروزه‌ای نسخه ۱ | `#5BB2AD` | C60 M8 Y33 K0 – نزدیک به Pantone 570 C |
| سرمه‌ای نسخه ۲ | `#1F2C50` | C100 M85 Y35 K25 – نزدیک به Pantone 289 C |
| طلایی | `#BE8C3C` | C25 M45 Y95 K5 – نزدیک به Pantone 4028 C |
| مشکی متن | `#16203F` | C90 M75 Y40 K35 |

* فونت‌ها: **Montserrat** (لاتین) و **Vazirmatn** (فارسی/عربی)، هر دو با مجوز
  SIL Open Font License؛ فایل‌ها و متن مجوز در `fonts/`.

## نکات مهم قبل از چاپ / Before you print

1. **بارکد**: عدد فعلی `6261234567897` نمونه است (رقم کنترل طبق استاندارد EAN‑13
   محاسبه شده، پس اسکن می‌شود اما متعلق به شما نیست). کد GS1 واقعی را در
   `utils/theme.py` مقدار `BARCODE_DIGITS` بگذارید و دوباره بسازید.
2. **QR**: به `https://www.shaparak-tissue.com` اشاره می‌کند؛ آدرس را در
   `theme.WEBSITE_URL` تغییر دهید.
3. **نشان استاندارد ایران**: نشان داخل فایل یک جانگهدار طراحی‌شده است. فایل رسمی
   سازمان ملی استاندارد و همچنین لوگوی رسمی گواهی ISO صادرکننده‌تان را جایگزین کنید.
4. پهنای خط‌های مو (مثل شیارهای دوخت و کادر سایزها) حداقل ۰٫۲ میلی‌متر است؛ اگر
   چاپخانه حداقل بیشتری می‌خواهد، در `utils/panels.py` اصلاح کنید.

## ساخت دوباره‌ی فایل‌ها / Rebuilding

```bash
python -m venv .venv && source .venv/bin/activate   # ویندوز: .venv\Scripts\activate
pip install cairosvg uharfbuzz fonttools qrcode
cd design/shaparak-pro
python generate.py            # همه‌ی خروجی‌ها در output/ ساخته می‌شوند
python generate.py --dpi 300  # پیش‌نمایش با کیفیت بالاتر
```

کد در پوشه‌ی `utils/` سازمان‌دهی شده است:

| فایل | نقش |
| --- | --- |
| `theme.py` | رنگ‌ها، اندازه‌ها و تمام متن‌های روی بسته |
| `svgdoc.py` | نویسنده‌ی SVG با واحد میلی‌متر و گروه‌های نام‌دار |
| `typography.py` | چیدمان متن، الگوریتم دوطرفه (bidi) و تبدیل متن به منحنی با HarfBuzz |
| `icons.py` | کتابخانه‌ی آیکون‌های برداری |
| `artwork.py` | پروانه، دوخت‌ها، بارکد EAN‑13، QR و نشان‌ها |
| `panels.py` | چیدمان پنل رو و پشت |

برای تغییر متن‌ها فقط `theme.py` را ویرایش کنید؛ اندازه‌ی فونت‌ها خودکار با عرض ستون
تطبیق داده می‌شود.
