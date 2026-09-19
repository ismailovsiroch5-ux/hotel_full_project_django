from django.urls import include, path
from django.contrib.auth import views as auth_views
from payme.views import PaymeWebHookAPIView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('book/<int:room_type_id>/', views.book_room, name='book_room'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('menu/', views.menu, name='menu'),
    path('jamoamiz/', views.our_team, name='our_team'),
    path('payme/update/', PaymeWebHookAPIView.as_view()),
    path('click/', include('click_uz.urls')),
    path('payment/<int:booking_id>/', views.start_payment, name='start_payment'),
    path('savat/qoshish/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('savat/ochirish/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('savat/', views.cart_view, name='cart_view'),
    path('savat/tasdiqlash/', views.checkout_order, name='checkout_order'),
    path('zakazlarim/', views.my_orders, name='my_orders'),
]
