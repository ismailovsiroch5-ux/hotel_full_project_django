from django.contrib import admin
from .models import RoomType, Room, Booking, MenuCategory, MenuItem, Chef, Administrator

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'price_per_night', 'capacity', 'has_wifi', 'has_breakfast')
    search_fields = ('title', 'description')
    list_filter = ('has_wifi', 'has_breakfast', 'has_air_conditioner')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'room_type', 'is_active')
    list_filter = ('room_type', 'is_active')
    search_fields = ('number',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'room', 'check_in', 'check_out', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'check_in', 'check_out')
    search_fields = ('user__username', 'room__number')
    date_hierarchy = 'check_in'


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')

@admin.register(Chef)
class ChefAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialty', 'experience_years', 'order')
    ordering = ('order',)

@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'order')
    ordering = ('order',)