from rest_framework import serializers
from .models import *

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        exclude = ['id', 'user', 'vcode']

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        exclude = ['id']

class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        exclude = ['id']