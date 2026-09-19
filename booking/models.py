from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date

class RoomType(models.Model):
    title = models.CharField(max_length=100, verbose_name="Xona Turi")
    description = models.TextField(verbose_name="Tavsif va Ta'rif")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bir kecha narxi ($)")
    capacity = models.PositiveIntegerField(default=2, verbose_name="Sig'imi (kishi)")
    image = models.ImageField(upload_to='rooms/', verbose_name="Rasm", blank=True, null=True)

    # Qulayliklar
    has_wifi = models.BooleanField(default=True, verbose_name="Bepul Wi-Fi")
    has_tv = models.BooleanField(default=True, verbose_name="Smart TV")
    has_air_conditioner = models.BooleanField(default=True, verbose_name="Konditsioner")
    has_breakfast = models.BooleanField(default=False, verbose_name="Shved stoli nonushta")

    def __str__(self):
        return f"{self.title} - ${self.price_per_night}/kecha"

    class Meta:
        verbose_name = "Xona Turi"
        verbose_name_plural = "Xona Turlari"


class Room(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name="Xona Raqami")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms', verbose_name="Xona Turi")
    is_active = models.BooleanField(default=True, verbose_name="Xizmatda (Aktiv)")

    def __str__(self):
        return f"Xona #{self.number} ({self.room_type.title})"

    class Meta:
        verbose_name = "Xona"
        verbose_name_plural = "Xonalar"


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Tasdiqlangan'),
        ('cancelled', 'Bekor qilingan'),
        ('completed', 'Yakunlangan'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name="Foydalanuvchi")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="Xona")
    check_in = models.DateField(verbose_name="Kelish sanasi")
    check_out = models.DateField(verbose_name="Ketish sanasi")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Jami Summa ($)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed', verbose_name="Holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    PAYMENT_METHOD_CHOICES = (
        ('click', 'Click'),
        ('payme', 'Payme'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', "To'lanmagan"),
        ('paid', "Oldindan to'lov qilingan"),
        ('failed', "To'lov amalga oshmadi"),
    )

    prepayment_percent = models.PositiveIntegerField(
        choices=[(30, "30%"), (50, "50%")],
        default=30,
        verbose_name="Oldindan to'lov foizi"
    )
    prepaid_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Oldindan to'langan summa ($)"
    )
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES,
        blank=True, null=True, verbose_name="To'lov turi"
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES,
        default='unpaid', verbose_name="To'lov holati"
    )
    transaction_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Tranzaksiya ID"
    )

    def clean(self):
        if self.check_in and self.check_out:
            if self.check_in >= self.check_out:
                raise ValidationError("Ketish sanasi kelish sanasidan keyin bo'lishi shart!")
            if self.check_in < date.today():
                raise ValidationError("O'tib ketgan sanaga bron qilib bo'lmaydi!")

            # Double Booking Guards (Overbooking ga yo'l qo'ymaslik filtri)
            overlapping = Booking.objects.filter(
                room=self.room,
                status__in=['pending', 'confirmed'],
                check_in__lt=self.check_out,
                check_out__gt=self.check_in
            ).exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError("Ushbu xona ko'rsatilgan sanalarda allaqachon bron qilingan!")

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out and self.room_id:
            nights = (self.check_out - self.check_in).days
            if nights > 0:
                self.total_price = nights * self.room.room_type.price_per_night
                self.prepaid_amount = (self.total_price * self.prepayment_percent) / 100
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bron #{self.id}: {self.user.username} - Xona {self.room.number}"

    class Meta:
        verbose_name = "Bron"
        verbose_name_plural = "Bronlar"


class MenuCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Turkum nomi")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Menyu Turkumi"
        verbose_name_plural = "Menyu Turkumlari"
        ordering = ['order']


class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items', verbose_name="Turkum")
    name = models.CharField(max_length=150, verbose_name="Taom nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narxi ($)")
    image = models.ImageField(upload_to='menu/', blank=True, null=True, verbose_name="Rasm")
    is_available = models.BooleanField(default=True, verbose_name="Mavjud")

    def __str__(self):
        return f"{self.name} - ${self.price}"

    class Meta:
        verbose_name = "Menyu Taomi"
        verbose_name_plural = "Menyu Taomlari"


class Chef(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="F.I.Sh")
    specialty = models.CharField(max_length=150, verbose_name="Mutaxassisligi")
    bio = models.TextField(blank=True, verbose_name="Qisqacha ma'lumot")
    photo = models.ImageField(upload_to='staff/chefs/', blank=True, null=True, verbose_name="Rasm")
    experience_years = models.PositiveIntegerField(default=0, verbose_name="Tajriba (yil)")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Oshpaz"
        verbose_name_plural = "Oshpazlar"
        ordering = ['order']


class Administrator(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="F.I.Sh")
    position = models.CharField(max_length=150, verbose_name="Lavozimi")
    bio = models.TextField(blank=True, verbose_name="Qisqacha ma'lumot")
    photo = models.ImageField(upload_to='staff/admins/', blank=True, null=True, verbose_name="Rasm")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Administrator"
        verbose_name_plural = "Administratorlar"
        ordering = ['order']

class FoodOrder(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('preparing', 'Tayyorlanmoqda'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilingan'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_orders', verbose_name="Foydalanuvchi")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='food_orders', verbose_name="Bron")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holati")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Jami summa ($)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Buyurtma vaqti")

    def __str__(self):
        return f"Zakaz #{self.id} - {self.user.username} (Xona {self.booking.room.number})"

    class Meta:
        verbose_name = "Zakaz"
        verbose_name_plural = "Zakazlar"
        ordering = ['-created_at']


class FoodOrderItem(models.Model):
    order = models.ForeignKey(FoodOrder, on_delete=models.CASCADE, related_name='items', verbose_name="Zakaz")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name="Taom")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Soni")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narxi (buyurtma paytida)")

    def get_subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    class Meta:
        verbose_name = "Zakaz Taomi"
        verbose_name_plural = "Zakaz Taomlari"
