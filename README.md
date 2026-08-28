# TikTok Username Checker

أداة فحص توفر أسماء المستخدمين على منصة TikTok بسرعة عالية مع دعم البروكسيات وإشعارات التليجرام.
High-speed TikTok username availability checker with multi-proxy support and Telegram notifications.

---

## Warning / تنبيه هام

**يمنع منعاً باتاً إزالة حقوق المطور.**
**Removal of developer rights/credits is strictly prohibited.**

- **Programmer:** `@umw_m`

---

## Arabic Guide / الدليل العربي

### 1. طريقة الحصول على البروكسي
1. قم بزيارة موقع [SmailPro](https://smailpro.com/temporary-email) للحصول على بريد Gmail مؤقت.
2. قم بإنشاء حساب في موقع [SparkProxy](https://www.sparkproxy.io/).
3. انسخ بيانات البروكسي بالصيغة التالية: `user:password@ip:port` وضعه داخل ملف `proxy.txt`.

### 2. إعداد ملف التكوين (config.txt)
قم بتعديل البيانات داخل ملف `config.txt`:
```ini
RATE_LIMIT=200
THREADS_PER_PROXY=100
TG_TOKEN=
TG_CHAT_ID=
```
- `RATE_LIMIT`: عدد الطلبات في الثانية لكل بروكسي.
- `THREADS_PER_PROXY`: عدد المسارات (Threads) لكل بروكسي.
- `TG_TOKEN`: توكن بوت التليجرام الخاص بك (من @BotFather).
- `TG_CHAT_ID`: آيدي المحادثة أو القناة لاستقبال المتاحات (من @userinfobot).

### 3. ملف اليوزرات المقلتشة (glitch.txt)
عند اكتشاف يوزر يظهر أنه متاح عند الفحص ولكن لا يمكن حجزه أو تثبيته داخل التطبيق، قم بإضافته في ملف `glitch.txt` (كل يوزر في سطر) لتتخطاه الأداة تلقائياً وعدم تكرار فحصه أو إرساله.

### 4. طريقة التشغيل
1. تثبيت الحزم المطلوبة:
   ```bash
   pip install -r requirements.txt
   ```
2. توليد قائمة اليوزرات الرباعية في `users.txt` (اختياري):
   ```bash
   python gen.py
   ```
3. تشغيل الأداة:
   ```bash
   python main.py
   ```

### 5. المخرجات
- `good.txt`: يتم حفظ اليوزرات المتاحة تلقائياً في هذا الملف.
- تليجرام: إرسال إشعار فوري عند صيد أي يوزر متاح.

---

## English Guide / الدليل الإنجليزي

### 1. Proxy Setup
1. Visit [SmailPro](https://smailpro.com/temporary-email) to generate a temporary Gmail address.
2. Create an account on [SparkProxy](https://www.sparkproxy.io/).
3. Copy proxies in `user:password@ip:port` format and paste them into `proxy.txt`.

### 2. Configuration (config.txt)
Set your parameters inside `config.txt`:
```ini
RATE_LIMIT=200
THREADS_PER_PROXY=100
TG_TOKEN=
TG_CHAT_ID=
```
- `RATE_LIMIT`: Max requests per second per proxy.
- `THREADS_PER_PROXY`: Number of threads per proxy.
- `TG_TOKEN`: Telegram bot API token (from @BotFather).
- `TG_CHAT_ID`: Telegram chat/channel ID (from @userinfobot).

### 3. Glitched Usernames List (glitch.txt)
If a username shows as available during checking but cannot be claimed in TikTok, add it to `glitch.txt` (one username per line). The tool will automatically skip all usernames listed in this file.

### 4. Installation & Execution
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate 4-character usernames list into `users.txt` (Optional):
   ```bash
   python gen.py
   ```
3. Run the checker:
   ```bash
   python main.py
   ```

### 5. Output
- `good.txt`: Available usernames are saved automatically here.
- Telegram: Instant notifications sent when hits are found.

---

## Rights & Credits / الحقوق

- **Programmer / المطور:** `@umw_m`
- **تنبيه:** يمنع منعاً باتاً إزالة حقوق المطور أو تعديلها.
- **Notice:** Removal or modification of developer credits is strictly prohibited.
