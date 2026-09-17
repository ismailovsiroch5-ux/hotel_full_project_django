from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from datetime import datetime, date
from .models import RoomType, Room, Booking, MenuCategory, Chef, Administrator
from .forms import UserRegisterForm
from .forms import BookingForm

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

    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
    room_type = get_object_or_404(RoomType, pk=pk)
    today = date.today().isoformat()
    return render(request, 'booking/room_detail.html', {'room_type': room_type, 'today': today})

@login_required
def book_room(request, room_type_id):
    room_type = get_object_or_404(RoomType, id=room_type_id)

    if request.method == 'POST':
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Iltimos, sanalarni to'g'ri shaklda kiriting!")
            return redirect('room_detail', pk=room_type_id)

        if check_in >= check_out or check_in < date.today():
            messages.error(request, "Xato: Ketish sanasi kelish sanasidan keyin va bugungi kundan kelajakda bo'lishi shart!")
            return redirect('room_detail', pk=room_type_id)

        # DEBUG START -----------------------------------------
        print("=" * 50)
        print("DEBUG: room_type_id (URLdan) =", room_type_id)
        print("DEBUG: room_type =", room_type, "| room_type.id =", room_type.id)
        print("DEBUG: check_in =", check_in, "| check_out =", check_out)

        # Tanlangan xona turidagi aktiv xonalarni topamiz
        available_rooms = Room.objects.filter(room_type=room_type, is_active=True)
        print("DEBUG: available_rooms count =", available_rooms.count())
        for r in available_rooms:
            print(f"DEBUG:   room = {r} | id={r.id} | is_active={r.is_active} | room_type_id={r.room_type_id}")

        assigned_room = None

        for room in available_rooms:
            overlapping = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out,
                check_out__gt=check_in
            )
            print(f"DEBUG:   checking room {room} -> overlap.exists() = {overlapping.exists()}")
            for b in overlapping:
                print(f"DEBUG:      conflicting booking id={b.id} | {b.check_in} - {b.check_out} | status={b.status}")
            if not overlapping.exists():
                assigned_room = room
                break

        print("DEBUG: FINAL assigned_room =", assigned_room)
        print("=" * 50)
        # DEBUG END -------------------------------------------

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
                total_price=0  # save() metodi ichida hisoblanadi
            )
            booking.save()
            messages.success(request, f"Muvaffaqiyatli bron qilindi! Sizga joylashtirilgan xona: #{assigned_room.number}")
            return redirect('my_bookings')
        except Exception as e:
            print("DEBUG: SAVE EXCEPTION ->", repr(e))
            messages.error(request, f"Bron qilishda xatolik yuz berdi: {e}")
            return redirect('room_detail', pk=room_type_id)

    return redirect('room_detail', pk=room_type_id)

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