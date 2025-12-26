from django.urls import path

from .views import (
    DashboardView,
    UserLoginView,
    UserLogoutView,
    UserRegisterView,
    email_my_data,
)

app_name = "accounts"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("privacy/email-my-data/", email_my_data, name="email_my_data"),
]
