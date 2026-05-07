# 🎬 KinoBot — Professional Telegram Kino Bot

AIogram 3 asosida yozilgan, clean architecture bilan professional Telegram kino boti.

---

## 🚀 O'rnatish (Lokal)

### 1. Repository clone qilish

```bash
git clone https://github.com/yourname/kinobot.git
cd kinobot
```

### 2. Virtual muhit yaratish

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. `.env` faylini sozlash

```bash
cp .env.example .env
```

`.env` faylini oching va o'z ma'lumotlaringizni kiriting:

```env
BOT_TOKEN=your_bot_token_here
ADMINS=123456789,987654321
DB_URL=sqlite+aiosqlite:///./kinobot.db
CHANNELS=-1001234567890
```

### 5. Botni ishga tushirish

```bash
python bot.py
```

---

## ☁️ Render.com da Deploy Qilish (Bepul va Ma'lumotlar Saqlanadi)

Render.com da **PostgreSQL** ishlatib, ma'lumotlaringizni abadiy saqlashingiz mumkin.

### 1. GitHub ga yuklash

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourname/kinobot.git
git push -u origin main
```

### 2. Render.com da account yaratish

1. [Render.com](https://render.com) ga kiring va "Get Started for Free" tugmasini bosing
2. GitHub hisobingiz bilan kiring

### 3. PostgreSQL ma'lumotlar bazasini yaratish

1. Render panelida **"New +"** tugmasini bosing
2. **"PostgreSQL"** ni tanlang
3. Sozlamalar:
   - **Name**: `kinobot-db`
   - **Database**: `kinobot`
   - **User**: `kinobot`
   - **Region**: eng yaqin joyni tanlang
   - **PostgreSQL Version**: default
4. **"Create Database"** tugmasini bosing
5. Ma'lumotlar bazasi yaratilgandan so'ng, **"Connection String"** ni ko'chirib oling (keyin kerak bo'ladi)

### 4. Web Service yaratish

1. Render panelida **"New +"** tugmasini bosing
2. **"Web Service"** ni tanlang
3. GitHub repozitoriyangizni tanlang (`kinobot`)
4. Sozlamalar:
   - **Name**: `kinobot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. **Environment Variables** qismiga quyidagilarni qo'shing:
   - `BOT_TOKEN` = Telegram BotFather dan olgan tokeningiz
   - `ADMINS` = Admin Telegram ID laringiz (vergul bilan)
   - `CHANNELS` = Majburiy obuna kanallari ID lari (vergul bilan, masalan: `-1001234567890`)
   - `DATABASE_URL` = (3-bosqichda olgan Connection String, `postgresql+asyncpg://...` ko'rinishida bo'lishi kerak)
6. **"Create Web Service"** tugmasini bosing

### 5. Avtomatik Deploy (render.yaml bilan)

Agar `render.yaml` fayli repozitoriyada bo'lsa, Render avtomatik ravishda:
- Web Service yaratadi
- PostgreSQL bazasini yaratadi
- `DATABASE_URL` ni avtomatik ulaydi

Shunchaki GitHub ga push qiling va Renderda "New +" -> "Blueprint" ni tanlang, repozitoriyani tanlang.

### ⚠️ Muhim eslatma

- **SQLite** (sqlite+aiosqlite://) faqat lokal kompyuterda ishlatilsin
- **Render.com da SQLite ishlamaydi** — har qayta ishga tushganda barcha ma'lumotlar o'chib ketadi!
- **PostgreSQL** ishlating — Render bepul PostgreSQL beradi va ma'lumotlar saqlanadi

---

## 📁 Loyiha tuzilmasi

```
kinobot/
├── app/
│   ├── handlers/
│   │   ├── users/        → Foydalanuvchi handlerlari
│   │   └── admin/        → Admin handlerlari
│   ├── keyboards/
│   │   ├── inline/       → Inline tugmalar
│   │   └── reply/        → Reply tugmalar
│   ├── middlewares/      → Middleware'lar
│   ├── filters/          → Admin filter
│   ├── states/           → FSM state'lari
│   ├── database/
│   │   ├── models/       → SQLAlchemy modellari
│   │   ├── queries/      → DB so'rovlari
│   │   └── db.py         → DB ulanish
│   ├── config/           → Sozlamalar
│   └── loader.py         → Bot va Dispatcher
├── bot.py                → Kirish nuqtasi
├── requirements.txt
└── .env.example
```

---

## 🎬 Kino tizimi

- Admin FSM orqali kino qo'shadi
- Video Telegram `file_id` orqali saqlanadi
- Kod, nom, janr bo'yicha qidiruv
- Pagination (5 ta kino / sahifa)

---

## 🔒 Majburiy obuna

- Har bir xabar/callback oldidan kanalga obuna tekshiriladi
- Obuna bo'lmagan foydalanuvchi bloklangan
- Admin panel orqali kanallar qo'shiladi/o'chiriladi

---

## 📢 Broadcast

- Admin matn, rasm yoki video yuborishi mumkin
- Barcha foydalanuvchilarga avtomatik yuboriladi

---

## 🛡 Xavfsizlik

- Admin filter
- Anti-flood middleware (0.5s)
- Callback validation
- Async DB session management

---

## 🧰 Tech Stack

| Texnologiya | Versiya |
|------------|---------|
| Python     | 3.12    |
| AIogram    | 3.13    |
| SQLAlchemy | 2.0     |
| SQLite / PostgreSQL | — |
| aiosqlite  | 0.20    |

---

## 📞 Muallif

Loyiha [https://t.me/@ahadbek00] tomonidan yaratilgan.
