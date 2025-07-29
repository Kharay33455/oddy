from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Trade)
admin.site.register(Customer)
admin.site.register(Wallet)
admin.site.register(Ad)
admin.site.register(TemplateMessage)
admin.site.register(TradeMessage)
admin.site.register(Faq)
admin.site.register(TransactionRequest)
admin.site.register(DisputeMessage)