# Telegram Bot - Ro'yxatdan o'tish tizimi

To'liq funksional Telegram bot Docker va PostgreSQL bilan.

## Xususiyatlar

- ✅ Foydalanuvchilarni ro'yxatdan o'tkazish
- ✅ Telefon raqamini avtomatik qabul qilish
- ✅ Foydalanuvchi ismini saqlash
- ✅ PostgreSQL database
- ✅ To'liq Docker muhiti

## O'rnatish va ishga tushirish

### 1. Bot tokenini olish

1. Telegramda [@BotFather](https://t.me/BotFather) botiga o'ting
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username kiriting
4. Bot tokenini oling

### 2. Environment sozlash

`.env` faylini yarating:

```bash
cp .env.example .env
```

`.env` faylida bot tokenini kiriting:

```env
BOT_TOKEN=sizning_bot_tokeningiz
```

### 3. Docker bilan ishga tushirish

```bash
# Build va ishga tushirish
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f bot

# To'xtatish
docker-compose down

# To'xtatish va ma'lumotlarni o'chirish
docker-compose down -v
```

## Loyiha strukturasi

```
.
├── bot/
│   ├── main.py              # Asosiy fayl
│   ├── config.py            # Konfiguratsiya
│   ├── database/
│   │   ├── models.py        # Database modellari
│   │   └── database.py      # Database funksiyalari
│   ├── handlers/
│   │   └── start.py         # Start handler
│   └── keyboards/
│       └── reply.py         # Klaviatura tugmalari
├── Dockerfile               # Docker konfiguratsiya
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Python kutubxonalar
└── .env                    # Environment o'zgaruvchilar
```

## Botdan foydalanish

1. Botni Telegramda toping
2. `/start` buyrug'ini yuboring
3. Telefon raqamingizni yuboring (tugma orqali)
4. Ismingizni kiriting
5. Tayyor! Ro'yxatdan o'tdingiz! 🎉

## Database strukturasi

**users** jadvali:
- `id` - ID (primary key)
- `telegram_id` - Telegram user ID
- `username` - Telegram username
- `first_name` - Ism (Telegramdan)
- `last_name` - Familiya (Telegramdan)
- `phone_number` - Telefon raqam
- `preferred_name` - Foydalanuvchi o'zi kiritgan ism
- `language_code` - Til kodi
- `is_registered` - Ro'yxatdan o'tgan/o'tmagan
- `created_at` - Yaratilgan vaqt
- `updated_at` - O'zgartirilgan vaqt

## Texnologiyalar

- Python 3.11
- aiogram 3.4.1 (Telegram Bot framework)
- PostgreSQL 16
- Docker & Docker Compose
- SQLAlchemy (ORM)

## Yordam

Muammoga duch kelsangiz, loglarni tekshiring:

```bash
docker-compose logs -f bot
docker-compose logs -f postgres
```
