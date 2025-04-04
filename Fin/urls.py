from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login_user'),
    path('register/', views.register_user, name='register_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('register/otp/', views.otp_view, name='otp'),
    path('/register/otp/', views.register_user, name='register'),
    path('main/',views.first, name = 'first'),
    path('results/', views.result, name = 'result'),
    path('upload-transactions/', views.upload_transactions, name='upload_transactions'),
    path('api/recent-transactions/', views.recent_transactions, name='recent_transactions'),
    path('api/add-expense/', views.add_expense, name='add_expense'),
    path('send-paytm-otp/', views.send_paytm_otp, name='send_paytm_otp'),
    path('verify-paytm-otp/', views.verify_paytm_otp, name='verify_paytm_otp'),

    path('/', views.home, name='home'),
    path('login', views.login_user, name='login_user'),
    path('register', views.register_user, name='register_user'),
    path('logout', views.logout_user, name='logout_user'),
    path('register/otp', views.otp_view, name='otp'),
    path('/register/otp', views.register_user, name='register'),
    path('main',views.first, name = 'first'),
    path('results', views.result, name = 'result'),
    path('upload-transactions', views.upload_transactions, name='upload_transactions'),
    path('api/recent-transactions', views.recent_transactions, name='recent_transactions'),
    path('api/add-expense', views.add_expense, name='add_expense'),
    path('send-paytm-otp', views.send_paytm_otp, name='send_paytm_otp'),
    path('verify-paytm-otp', views.verify_paytm_otp, name='verify_paytm_otp'),
]