# 🎬 KinoBot — Professional Telegram Kino Bot

AIogram 3 asosida yozilgan, clean architecture bilan professional Telegram kino boti.

---

## 🚀 O'rnatish

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
