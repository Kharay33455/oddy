from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    email = models.EmailField()
    ratings = models.FloatField(null = True, blank = True)
    processingTime = models.IntegerField(null = True, blank = True)
    trades = models.IntegerField(default = 0)
    isBot = models.BooleanField(default = False)
    balance = models.FloatField(default = 0.0)
    emailVerified = models.BooleanField(default = False)
    vcode = models.CharField(max_length = 64, blank = True, null = True)
    idDocs = models.ImageField(upload_to = "verid", blank = True, null = True)
    idApproved = models.BooleanField(default = False)
    selfie = models.ImageField(upload_to = "verselfie" , blank = True, null = True)
    selfieApproved = models.BooleanField(default = False)

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
    time = models.DateTimeField(auto_now = True)
    successful = models.BooleanField(blank=True, null = True)
    buyerRating = models.CharField(max_length=1, blank=True, null = True)
    sellerRating = models.CharField(max_length= 1 , blank=True, null = True)
    timeToProcess = models.CharField(max_length = 5, blank=True, null = True)

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

    def __str__(self):
        return f"{self.customer.user.username}"

class Wallet(models.Model):
    wallet_net = models.CharField(max_length = 20)
    wallet_address = models.CharField(max_length = 50)

    def __str__(self):

        return f"Wallet {self.wallet_net}"
