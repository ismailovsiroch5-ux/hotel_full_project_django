# Grand Royal Hotel - Django & PostgreSQL Complete Project

Ushbu loyiha Django 4+, Bootstrap 5 va PostgreSQL (pgAdmin 4) asosida qurilgan mukammal va tayyor mehmonxona bron qilish tizimidir.

## Loyiha Texnologiyalari:
- **Backend**: Python, Django
- **Frontend**: HTML5, CSS3, Bootstrap 5, FontAwesome, JavaScript
- **Database**: PostgreSQL (pgAdmin 4)

---

## O'rnating va Ishga Tushirish Qadamlari:

### 1. ZIP faylni oching va papkaga kiring:
```bash
cd hotel_django_full_project
```

### 2. Virtual muhit (venv) yaratish va uni aktivlashtirish:
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Mac/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Kerakli paketlarni o'rnatish:
```bash
pip install django psycopg2-binary Pillow
```

### 4. PostgreSQL va pgAdmin 4 sozlamasi:
1. `pgAdmin 4` ni oching.
2. `hotel_db` nomli yangi Database yarating.
3. `hotel_project/settings.py` faylini ochib, `DATABASES` sozlamasiga pgAdmin parolingizni kiritib saqlang:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hotel_db',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_PGADMIN_PASSWORD',  # Shu yerga kiritiladi
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Bazaga migratsiyalarni o'tkazish:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Admin (Superuser) yaratish:
```bash
python manage.py createsuperuser
```

### 7. Serverni ishga tushirish:
```bash
python manage.py runserver
```

Sayt: http://127.0.0.1:8000/
Admin Panel: http://127.0.0.1:8000/admin/
