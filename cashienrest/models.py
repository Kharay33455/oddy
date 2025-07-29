from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    email = models.EmailField()
    ratings = models.FloatField(default = 8.01)
    processingTime = models.IntegerField(null = True, blank = True)
    trades = models.IntegerField(default = 0)
    isBot = models.BooleanField(default = False)
    balance = models.FloatField(default = 0.0)
    emailVerified = models.BooleanField(default = False)
    vcode = models.CharField(max_length = 64, blank = True, null = True)
    vcode_time = models.DateTimeField(blank = True, null = True)
    idDocs = models.ImageField(upload_to = "verid", blank = True, null = True)
    idApproved = models.BooleanField(default = False)
    selfie = models.ImageField(upload_to = "verselfie" , blank = True, null = True)
    selfieApproved = models.BooleanField(default = False)
    is_restricted = models.BooleanField(default = False)

    def __str__(self):
        return self.user.username

class Trade(models.Model):
    tradeId = models.CharField(max_length=20)
    buyerId = models.CharField(max_length=20)
    sellerId = models.CharField(max_length=20)
    amount = models.CharField(max_length=20)
    rates = models.CharField(max_length=10)
    # 1 is usd, 2 is cny, 3 is eur
    currency = models.CharField(max_length = 1)
    time = models.DateTimeField(auto_now_add = True)
    successful = models.BooleanField(blank=True, null = True)
    buyerRating = models.CharField(max_length=1, blank=True, null = True)   #rating received by buyer
    sellerRating = models.CharField(max_length= 1 , blank=True, null = True)    # rating received by seller
    timeToProcess = models.CharField(max_length = 5, blank=True, null = True)
    receipt = models.ImageField(upload_to="cashien/receipts", blank=True, null = True)

    # bank dets
    bank_name = models.TextField()
    receiver_name = models.TextField(null = True, blank = True)
    account_number = models.CharField(max_length = 30 , null = True, blank = True)
    qr_code = models.ImageField(upload_to = "qr", null = True, blank = True)
    remark = models.TextField(blank = True, null = True)

    # dispute
    is_disputed = models.BooleanField(blank = True, null = True)

    def __str__(self):
        return self.tradeId


class Ad(models.Model):
    adId = models.CharField(max_length = 30)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    # 1 is usd, 2 is cny, 3 is eur
    currency = models.CharField(max_length = 1)
    min_amount = models.IntegerField()
    max_amount = models.IntegerField()
    rates = models.FloatField()
    is_active = models.BooleanField(default = True)
    terms = models.TextField()
    
    # payment methods
    bank = models.BooleanField(default = True)
    alipay = models.BooleanField(default = False)
    wechatpay = models.BooleanField(default = False)
    paypal = models.BooleanField(default = False)
    wise = models.BooleanField(default = False)
    sepa = models.BooleanField(default = False)
    revolut = models.BooleanField(default = False)
    swift = models.BooleanField(default = False)
    payoneer = models.BooleanField(default = False)
    remitly = models.BooleanField(default = False)
    def __str__(self):
        return f"{self.customer.user.username}"


class PaymentMethod(models.Model):
    ad_id = models.ForeignKey(Ad, on_delete=models.CASCADE)
    payment = models.CharField(max_length=30)

    def __str__(self):
        return self.ad_id

class Wallet(models.Model):
    wallet_net = models.CharField(max_length = 20)
    wallet_address = models.CharField(max_length = 50)

    def __str__(self):

        return f"Wallet {self.wallet_net}"


class TemplateMessage(models.Model):
    message_id = models.CharField(max_length = 50)
    message_text = models.TextField()
    for_buyer = models.BooleanField(blank = True, null = True)

    def __str__(self):
        return f"{self.message_text} for {self.for_buyer}"

class TradeMessage(models.Model):
    trade = models.ForeignKey(Trade, on_delete = models.CASCADE)
    message_text = models.TextField()
    sender = models.ForeignKey(Customer, on_delete = models.CASCADE)
    time = models.DateTimeField()
    is_sent = models.BooleanField(default = True)

    def __str__(self):
        return f"Message for trade {self.trade.tradeId}"


class Faq(models.Model):
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return self.question

class TransactionRequest(models.Model):
    transaction_id = models.CharField(max_length = 30)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    transaction_address = models.TextField()
    is_deposit = models.BooleanField()
    amount = models.FloatField(blank = True, null = True)
    status = models.BooleanField(blank = True, null = True)
    remark = models.TextField(blank = True, null = True)
    time = models.DateTimeField(auto_now_add = True)
    completed = models.DateTimeField(blank = True, null = True)

    def __str__(self):
        return f"{self.customer.user.username} for {self.amount} at {self.time} -- {self.status}"


class DisputeMessage(models.Model):
    msg_id = models.CharField(max_length = 10)
    trade = models.ForeignKey(Trade, on_delete = models.CASCADE)
    text = models.TextField(blank = True, null = True)
    image = models.ImageField(blank = True, null = True, upload_to="dispute")
    sender = models.ForeignKey(Customer, on_delete = models.CASCADE)
    time = models.DateTimeField(auto_now = True)
    is_sent = models.BooleanField(default = True)

    def __str__(self):
        return f"Message for dispute {self.trade.tradeId}"