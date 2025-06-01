from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
import json, base64, random
from cashienrest import models as CashienModels
from cashienrest import serializers as CashienSerializers
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class CashienChatConsumer(AsyncWebsocketConsumer):


    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        
        cookie = self.scope['cookies']['token']
        
        user = await sync_to_async(self.validate_user)(self.room_name, cookie)
        
        if user:
        # Join room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        
    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == "new_text":
            message = text_data_json["text"]
            message_created = await sync_to_async(self.create_new_message)(message)
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat.message", "message": message_created}
            )
        
        if text_data_json['type'] == 'receipt':
            image_as_b64 = text_data_json['image']
            receipt = await sync_to_async(self.append_receipt)(image_as_b64)
            await self.channel_layer.group_send(
                self.room_group_name, {"type" : "receipt.message", "image_url": receipt}
            )
        
        if text_data_json['type'] == 'release':
            release_context = await sync_to_async(self.release_usdt)()
            await self.channel_layer.group_send(
                self.room_group_name, {"type":"release.message", "context":release_context}
            )



    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"type" : "new_text","message": message}))

    async def receipt_message(self, event):
        image_url = event['image_url']
        await self.send(text_data = json.dumps({"type":"receipt", "image_url":image_url}))


    async def release_message(self, event):
        context = event['context']
        await self.send(text_data = json.dumps({"type":"release", "context":context}))

    def validate_user(self, tradeId, cookie):
        
        user = Token.objects.get(key = cookie).user
        try:
            trade = CashienModels.Trade.objects.get(tradeId = tradeId)
        except Trade.DoesNotExist:
            return False

        cus = CashienModels.Customer.objects.get(user = user)
        if cus.id != int(trade.buyerId) and cus.id != int(trade.sellerId):
            return False
        else:
            return True

    def create_new_message(self, message_text):
        cookie = self.scope['cookies']['token']
        trade = CashienModels.Trade.objects.get(tradeId = self.room_name)
        cus = CashienModels.Customer.objects.get(user = Token.objects.get(key = cookie).user)
        new_message = CashienModels.TradeMessage.objects.create(trade = trade, message_text = message_text, sender = cus)
        new_message_data = CashienSerializers.TradeMessageSerializer(new_message).data
        new_message_data['sender']= cus.user.username
        return new_message_data

    def append_receipt(self, b64img):
        if b64img.startswith("data:image"):
            b64img = b64img.split(",")[1]
        image = ContentFile(base64.b64decode(b64img), name =f"TradeReceipt{self.room_name}.jpg")
        trade = CashienModels.Trade.objects.get(tradeId = self.room_name)
        trade.receipt = image
        trade.save()
        return trade.receipt.url
    
    def release_usdt(self):
        cookie = self.scope['cookies']['token']
        user = Token.objects.get(key = cookie).user
        trade = CashienModels.Trade.objects.get(tradeId = self.room_name)
        customer = CashienModels.Customer.objects.get(user = user)
        seller = CashienModels.Customer.objects.get(id = int(trade.sellerId))
        if customer.id == int(trade.buyerId):
            seller.balance += float(trade.amount)
            trade.successful = True
            trade.timeToProcess = int((timezone.now() - trade.time).total_seconds())
            seller.save()
            trade.save()
            context= {"time_to_process" : trade.timeToProcess}
            return context


class CashienDisputeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"{self.scope['url_route']['kwargs']['room_name']}"
        self.room_group_name = f"group_dispute_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        token = self.scope['cookies']['token']
        dispute_data = await sync_to_async(self.validate_user)(token)
        if dispute_data:
            await self.accept()
            await self.send(text_data = json.dumps({'type':"dispute_data","data" : dispute_data}))
            



    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if(text_data_json['type'] == "newMessage"):
            message = await sync_to_async(self.create_new_message)(text_data_json)
            await self.channel_layer.group_send(
                self.room_group_name,{"type":"new.message", "message" : message}
            )

    async def new_message(self, event):
        await self.send(text_data = json.dumps({"type":"new_message","data":event['message']}))

    def create_new_message(self, event):
        trade = CashienModels.Trade.objects.get(tradeId = self.room_name)
        customer = CashienModels.Customer.objects.get(user = Token.objects.get(key = self.scope['cookies']['token']).user)
        if(event['img'] == None):
            image = None
        else:
            img = event['img']
            if img.startswith("data:image"):
                img = img.split(",")[1]
            random_num = random.randint(10000, 9999999)
            image = ContentFile(base64.b64decode(img), name = f"dispute{random_num}.jpg")
        message = CashienModels.DisputeMessage.objects.create(text=event['text'], image = image, trade = trade, sender = customer)
        message_data = CashienSerializers.DisputeMessageSerializer(message).data
        message_data['sender'] = customer.user.username
        return message_data

    def validate_user(self, token):
        try:
            user = Token.objects.get(key = token).user
            customer = CashienModels.Customer.objects.get(user = user)
            trade = CashienModels.Trade.objects.get(tradeId = self.room_name)

            if int(trade.buyerId) != customer.id and int(trade.sellerId) != customer.id:
                return False
            else:
                trade_data = CashienSerializers.TradeSerializer(trade).data
                buyer = CashienModels.Customer.objects.get(id = int(trade_data['buyerId']))
                seller = CashienModels.Customer.objects.get(id = int(trade_data['sellerId']))
                
                dispute_messages = CashienSerializers.DisputeMessageSerializer(CashienModels.DisputeMessage.objects.filter(
                    trade = trade), many = True).data
                for message in dispute_messages:
                    if int(message['sender']) == buyer.id:
                        message['sender'] = buyer.user.username
                    
                    elif int(message['sender']) == seller.id:
                        message['sender'] = seller.user.username
                print(dispute_messages)
                return {"trade data" : trade_data, "messages" : dispute_messages}
        except Token.DoesNotExist:
            return False

