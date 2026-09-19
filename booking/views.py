from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from datetime import datetime, date

from .models import RoomType, Room, Booking, MenuCategory, MenuItem, Chef, Administrator, FoodOrder, FoodOrderItem
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
def get_active_booking(user):
    today = date.today()
    return Booking.objects.filter(
        user=user,
        status='confirmed',
        check_in__lte=today,
        check_out__gte=today
    ).first()


def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    cart[item_id_str] = cart.get(item_id_str, 0) + quantity
    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, f"{item.name} savatga qo'shildi!")
    return redirect('menu')


def remove_from_cart(request, item_id):
    cart = request.session.get('cart', {})
    cart.pop(str(item_id), None)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_view')


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for item_id_str, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id_str))
        except MenuItem.DoesNotExist:
            continue
        subtotal = item.price * quantity
        total += subtotal
        cart_items.append({'item': item, 'quantity': quantity, 'subtotal': subtotal})

    active_booking = None
    if request.user.is_authenticated:
        active_booking = get_active_booking(request.user)

    return render(request, 'booking/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'active_booking': active_booking,
    })


@login_required
def checkout_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Savatingiz bo'sh!")
        return redirect('menu')

    active_booking = get_active_booking(request.user)
    if not active_booking:
        messages.error(request, "Buyurtma berish uchun aktiv (joriy) broningiz bo'lishi shart!")
        return redirect('cart_view')

    order = FoodOrder.objects.create(user=request.user, booking=active_booking)
    total = 0

    for item_id_str, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id_str))
        except MenuItem.DoesNotExist:
            continue
        FoodOrderItem.objects.create(order=order, menu_item=item, quantity=quantity, price=item.price)
        total += item.price * quantity

    order.total_price = total
    order.save()

    request.session['cart'] = {}
    request.session.modified = True

    messages.success(request, f"Buyurtmangiz qabul qilindi! Xona #{active_booking.room.number}ga yetkaziladi.")
    return redirect('my_orders')


@login_required
def my_orders(request):
    orders = FoodOrder.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'booking/my_orders.html', {'orders': orders})


