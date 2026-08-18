"""
Roteamento para endpoints de Autenticação (/api/auth/).
"""
from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    MeView,
    SetPinView,
    UnlockPinView,
    ForgotPasswordView,
    ResetPasswordView,
    ActivateAccountView,
)

app_name = 'authentication'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('set-pin/', SetPinView.as_view(), name='set-pin'),
    path('unlock-pin/', UnlockPinView.as_view(), name='unlock-pin'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('activate-account/', ActivateAccountView.as_view(), name='activate-account'),
]
