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

class TemplateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateMessage
        exclude = ['id']

class TradeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeMessage
        exclude = ['id', 'trade']

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = "__all__"

class TransactionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionRequest
        exclude = ['id']
