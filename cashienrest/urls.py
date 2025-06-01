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
    path("verify-id", verify_id, name="verify_id"),
    path("init-new-trade/", init_new_trade, name="init_new_trade"),
    path("trade<slug:trade_id>/", trade, name="trade"),
    path("rate-transaction/", rate_transaction, name="rate-transaction"),
    path("get-cus-ads", get_cus_ads, name="get-cus-ads"),
    path("delete-ad/", delete_ad, name="delete_ad"),
    path("create-new-ad/", create_new_ad, name="create-new-ad"),
    path("get-faqs", get_faqs, name="get-faqs"),
    path("get-wallet-address", get_wallet_address, name="get_wallet_address"),
    path("handle-transaction-<slug:transaction_type>/", handle_transaction, name="handle_transaction"),
    path("reactivate-ad/", reactivate_ad, name="reactivate-ad"),
    path("reset-password/", reset_password, name="reset-password"),
    path("new-pass/<slug:otp>/", new_pass, name="new_pass"),
    path("init-new-qr-trade/", init_new_qr_trade, name="init_new_qr_trade"),
    path("socket-validate-user<slug:trade_id>", socket_validate_user, name="socket_validate_user"),
    path("socket-create-new-message/", create_new_message, name="create_new_message"),
    path("socket-append-receipt/", socket_append_receipt, name="socket_append_receipt"),
    path("socket-release-usdt/", socket_release_usdt, name="socket_release_usdt"),
    path("socket-get-dispute-data<slug:trade_id>", socket_get_dispute_data, name="socket-get-dispute-data"),
    path("socket-create-new-dispute-message/", create_new_dispute_message, name="create_new_dispute_message"),
]