from django.urls import path
from .views import *

app_name = "cashienrest"

urlpatterns = [
    path("login/", login_request, name= "login-request"),
    path("register/", registration_request, name="register"),
    path("fetch-user", fetch_user, name="fetch-user"),
    path("logout", logout_request, name="logout"),
    path("rankers", rankers, name='rankers'),
    path("create-ads", create_ads, name="create_ads"),
    path("get-ads", getAds, name="get-ads"),
    path("fetch-trades", fetch_trades, name="fetch-trades"),
    path("verify", verify, name="verify"),
    path("verify-id", verify_id, name="verify_id")
]