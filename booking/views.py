from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from datetime import datetime, date

from .models import RoomType, Room, Booking, MenuCategory, Chef, Administrator
from .forms import UserRegisterForm
from .forms import BookingForm

from payme import Payme
from click_up import ClickUp

payme = Payme(payme_id=settings.PAYME_ID)


def index(request):
    room_types = RoomType.objects.all()[:3]
    context = {
        'room_types': room_types,
        'today': date.today().isoformat()
    }
    return render(request, 'booking/index.html', context)


def room_list(request):
    room_types = RoomType.objects.all()
    return render(request, 'booking/rooms.html', {'room_types': room_types})


def room_detail(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk)
    today = date.today().isoformat()
    return render(request, 'booking/room_detail.html', {'room_type': room_type, 'today': today})


@login_required
def book_room(request, room_type_id):
    room_type = get_object_or_404(RoomType, id=room_type_id)

    if request.method == 'POST':
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        prepayment_percent = int(request.POST.get('prepayment_percent', 30))

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Iltimos, sanalarni to'g'ri shaklda kiriting!")
            return redirect('room_detail', pk=room_type_id)

        if check_in >= check_out or check_in < date.today():
            messages.error(request, "Xato: Ketish sanasi kelish sanasidan keyin va bugungi kundan kelajakda bo'lishi shart!")
            return redirect('room_detail', pk=room_type_id)

        # Tanlangan xona turidagi aktiv xonalarni topamiz
        available_rooms = Room.objects.filter(room_type=room_type, is_active=True)
        assigned_room = None

        for room in available_rooms:
            overlapping = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out,
                check_out__gt=check_in
            )
            if not overlapping.exists():
                assigned_room = room
                break

        if not assigned_room:
            messages.error(request, "Afsuski, tanlangan sanalarda ushbu toifadagi bo'sh xonalar qolmagan!")
            return redirect('room_detail', pk=room_type_id)

        # Bron yaratish
        try:
            booking = Booking(
                user=request.user,
                room=assigned_room,
                check_in=check_in,
                check_out=check_out,
                prepayment_percent=prepayment_percent
            )
            booking.save()
            messages.success(request, f"Bron yaratildi! Xona: #{assigned_room.number}. Endi oldindan to'lovni amalga oshiring.")
            return redirect('start_payment', booking_id=booking.id)
        except Exception as e:
            messages.error(request, f"Bron qilishda xatolik yuz berdi: {e}")
            return redirect('room_detail', pk=room_type_id)

    return redirect('room_detail', pk=room_type_id)


@login_required
def start_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        method = request.POST.get('payment_method')
        booking.payment_method = method
        booking.save()

        if method == 'payme':
            pay_link = payme.initializer.generate_pay_link(
                id=booking.id,
                amount=int(booking.prepaid_amount * 100),  # Payme summani tiyinda kutadi
                return_url=request.build_absolute_uri('/my-bookings/')
            )
            return redirect(pay_link)

        elif method == 'click':
            click_up = ClickUp(
                service_id=settings.CLICK['SERVICE_ID'],
                merchant_id=settings.CLICK['MERCHANT_ID'],
            )
            pay_link = click_up.initializer.generate_pay_link(
                id=booking.id,
                amount=float(booking.prepaid_amount),
                return_url=request.build_absolute_uri('/my-bookings/')
            )
            return redirect(pay_link)

        else:
            messages.error(request, "Iltimos, to'lov turini tanlang!")
            return redirect('start_payment', booking_id=booking.id)

    return render(request, 'booking/start_payment.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'booking/my_bookings.html', {'bookings': bookings})


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz!")
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def menu(request):
    categories = MenuCategory.objects.prefetch_related('items').all()
    return render(request, 'booking/menu.html', {'categories': categories})


def our_team(request):
    chefs = Chef.objects.all()
    admins = Administrator.objects.all()
    return render(request, 'booking/our_team.html', {'chefs': chefs, 'admins': admins})