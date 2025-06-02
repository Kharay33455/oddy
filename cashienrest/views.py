from django.utils import timezone
from django.core.files.base import ContentFile
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .models import *
from .serializers import *
import re, random, string, base64, json


def check_trade_viability(trade):
    time_left = int(900 - (timezone.now() - trade.time).total_seconds())

    if time_left <= 0 and trade.successful == None and not trade.receipt:
        trade.successful = False
        trade.save()    

def generate_ad_data(customer):
    # serialize
    data = AdSerializer(Ad.objects.filter(customer = customer), many = True).data
    # append name
    for d in data:
        d['customer'] = customer.user.username
    return data

def gen_cus_data(_user):
    cus_data = CustomerSerializer(Customer.objects.get(user = _user)).data
    cus_data['user'] = _user.username
    
    return cus_data

def gen_trade_data(cus, trade):
    if int(trade.sellerId) != cus.id and int(trade.buyerId) != cus.id:
        None
    check_trade_viability(trade)
    time_left = int(900 - (timezone.now() - trade.time).total_seconds())
    trade_data = TradeSerializer(trade).data
    trade_data['buyerId'] = Customer.objects.get(pk = trade.buyerId).user.username
    trade_data['sellerId'] = Customer.objects.get(pk = trade.sellerId).user.username
    trade_data['time_left'] = time_left
    return trade_data

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def validate(_str, _acceptables):
    for _ in _str:
        if _ not in _acceptables:
            return False
    return True

def validate_ad_input(data):
    acceptables = ['0','1','2','3','4','5','6','7','8','9']
    if not validate(data['min'], acceptables):
        return {"status":False, "msg":"Minimum value must be a number"}
    if not validate(data['max'], acceptables):
        return {"status":False, "msg":"Maximum value must be a number"}
    
    try:
        data['rates'] = float(data['rates'])
    except ValueError:
        return {"status":False, "msg":"Rates must be a valid number"}
    
    if int(data['currency']) <1 or int(data['currency']) > 3:
        return {"status":False, "msg":"An unexpected error has occured."}

    safe = False
    for method, status in data['paymentMethods'].items():
        if status == True:
            safe = True
    
    if safe == False:
        return {"status":False, "msg" : "You need to select at least one active payment method."}

    if str(data["terms"])== "":
        return {"status":False, "msg" : "You need to specify valid terms for your buyers."}
    else:
        data['terms'] = str(data['terms'])

    return {"status":True, "data":data}
    


# Create your views here.

@api_view(['POST'])
def login_request(request):
    username = str(request.data['username']).strip()
    password = str(request.data['password']).strip()
    try:
        username = Customer.objects.get(email = username).user.username
    except Customer.DoesNotExist:
        pass
    user = authenticate(username = username, password = password)
    if user is not None:
        token, created = Token.objects.get_or_create(user = user)
        cus_data = gen_cus_data(user)
        context = {'key':token.key, "cus":cus_data}
        return Response(context, status = 200)
    else:
        return Response({"msg":"Invalid username or password"}, status = 403)
    


@api_view(['POST'])
def registration_request(request):
    # extract data from form
    username = str(request.data['username']).strip()
    email = str(request.data['email']).strip()
    password1 = str(request.data['password1']).strip()
    password2 = str(request.data['password2']).strip()
    confirm = request.data['terms']

    # validate
    acceptables = ['A', 'S', 'D', 'F', 'G', 'H','J', 'K', 'L', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '!', '@', '#', '$', '%', '*', '_', '+', '=', '-', '.', ',','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m']
    if not validate(username, acceptables):
        return Response({'msg':"Username contains unallowed characters."}, status = 403)
    if len(username) < 1:
        return Response({'msg' : "Username cannot be blank."}, status = 403)
    
    if not is_valid_email(email):
        return Response({'msg':"Invalid email format"}, status = 403)
    if not validate(password1, acceptables):
        return Response({'msg':"Password contains unallowed characters."}, status = 403)
    if len(password1) < 1:
        return Response({'msg' : "Password must be at least 8 characters."}, status = 403)        
    if password1 != password2:
        return Response({'msg':"Passwords did not match"}, status = 403)
    if confirm != True:
        return Response({'msg':"You must accept terms to continue"}, status = 403)
    
    # check if user already exists with details
    possibles = Customer.objects.filter(email = email)
    if possibles:
        return Response({'msg':"A user with this email already exists."}, status = 403)
    try:
        user = User.objects.create(username = username, password = password1)
    except IntegrityError:
        return Response({'msg':"A user with this username already exists."}, status = 403)
    
    # create customer
    cus = Customer.objects.create(user = user, email = email)
    # authenticate
    token = Token.objects.create(user = user)
    # create context and return
    cus_data = CustomerSerializer(cus).data
    cus_data['user'] = user.username
    context = {'key' : token.key, 'cus' : cus_data}
    return Response(context, status = 200)

@api_view(['GET'])
def logout_request(request):
    key = request.headers['Authorization']
    try:
        Token.objects.get(key = key).delete()
    except Token.DoesNotExist:
        return Response(status = 403)
    return Response(status = 200)

@api_view(['GET'])
def fetch_user(request):
    key = request.headers['Authorization']
    try:
        token = Token.objects.get(key = key)
        cus = gen_cus_data(token.user)
        return Response({"cus":cus}, status = 200)
    except Token.DoesNotExist:
        return Response(status = 204)

@api_view(['GET'])
def rankers(request):
    ethnic = [
    # Chinese-style (25)
    "li_wei88", "zhangfei_22", "wang_jun7", "chen_minghao", "xiao_ling23",
    "yu_zhilan", "tangxiaoyu", "lin_haoran", "zhoumei_33", "sun_liang88",
    "liu_jie77", "gao_yuting", "hanbo_21", "fengmei_19", "guowenli",
    "he_yao16", "meng_xinyue", "pei_lei12", "qianweiguo", "rao_jingjing",
    "shi_lei202", "xuyibo_8", "yang_lina33", "zheng_mingli", "du_chen89",

    # European-style (25)
    "lukas_meyer93", "elena_richter", "mateusz_kowalski", "sophie_dubois",
    "henrik_olsen21", "nina_bauer88", "tomas_novak77", "emil_ivanov_",
    "anna_kralova", "dimitri_petrov55", "katrin_muller91", "giorgio_rossi7",
    "karl_heinz123", "janek_kubik", "ines_papadopoulos", "jakob_braun01",
    "victor_belmont", "laura_weber45", "stephan_mazur", "magda_fischer77",
    "mario_luciano", "bela_szabo23", "teresa_nowak", "noemi_reich", "ivan_stefanov",

    # American-style (25)
    "jake_henderson1", "madison_smith_99", "brad_jackson42", "ashley_taylor_",
    "kyle_brown1987", "riley_martin08", "brooklyn_lee33", "chase_walker17",
    "harper_davis", "tyler_evans99", "emma_thomas24", "carter_moore",
    "avery_jameson", "zoe_anderson03", "nathan_clark22", "skylar_roberts",
    "aiden_wilson7", "hailey_white_88", "logan_kelly10", "morgan_hall",
    "blake_cooper_", "sierra_wood93", "landon_scott_", "julian_adams",
    "peyton_morris44",

    # Jewish-style (25)
    "david_levy10", "sarah_goldstein22", "isaac_koenigsberg", "rachel_stein_",
    "moshe_rosenberg88", "miriam_cohen91", "yael_greenberg33", "jacob_blum",
    "tamar_aronson", "noah_friedman1", "eliezer_katz7", "shira_weiss22",
    "hannah_lieberman", "avraham_ziv", "esther_schwartz", "yoni_goldfarb_",
    "naomi_feldman33", "menachem_benari", "leah_klugman", "ari_kaplan12",
    "rivka_dayan", "baruch_reisman", "simon_eldar", "malki_segal", "ronen_mazal"
    ]

    genz_usernames = [
    "cloudvibez", "snackqueen22", "xoxo_nova", "sleepyfrogg", "dizzy.dreamz",
    "vibecheck420", "noodlelord", "toxic.glow", "pastelghost", "berrybloop",
    "crush.exe", "yuhboi_max", "skrrtskrrt77", "owo_peachy", "gothgrl666",
    "m00nch1ld", "404baddie", "glitchwitch", "cyberbae", "starrykitten",
    "ravioli_riot", "simp_sauce", "uwusniper", "lilcryptid", "sadfroggirl",
    "yeetjuice", "p1xelduck", "s0ftboi7", "shrekprincess", "jelly._belly",
    "e_lite420", "cozyg0blin", "sleepy.nacho", "b33pb33p", "peach.soda",
    "e-gurl._zz", "bagel.kween", "crispytoes", "velcro_vibes", "altf4_luv",
    "picklewitch_", "lava_lampz", "snailmail666", "rainbow.k1tty", "gummybat",
    "whatevzbro", "icantmath", "pls_stop_me", "drama.llama9", "unicornscry2",
    "l33tfairy", "softxxcore", "zooted_and_rooted", "crocsnocks", "drippin._tea",
    "yeetfleet", "shad3dtea", "fluff.n.spice", "memezforever", "goose.god",
    "mayo_freak", "vampire.kiddo", "t0xic_cereal", "ratkid_online", "d00mflower",
    "lofi.socks", "hella_hungry", "sk8rbunny", "cosmic.avocado", "b00giemonsta",
    "shrimpwrld", "sushi_panic", "v1rus.baby", "slothvibes24", "emo._pickle",
    "basic.boi", "ouchiepouchie", "flopqueen7", "grape.crunch", "helloimweird",
    "oof_machine", "star._nerd", "edgy_mocha", "toasterkiss", "notclickbait99",
    "zoomerd00d", "boing._boing", "crankyy.bee", "glowup.fail", "kdrama._tearz",
    "bunnyonfire", "midcore_lord", "sippinsprite", "hearteyesxoxo", "trashcanchic",
    "sleepy.chaos", "bubbletroublez", "m0od_ring", "vibecube", "woke.up.late"
    ]

    usernames = genz_usernames + ethnic

    def createUsers(_usernames):
        for _ in _usernames:
            password = str(random.randint(1638767383876,9636366463467363768))
            try:
                user, created = User.objects.get_or_create(username = _,  password = password)
                customer, created = Customer.objects.get_or_create(user = user, email = f"{_}+@gmail.com")
            except IntegrityError:
                pass
    
    def generate_rankers(amt, floor):
        users = Customer.objects.all()
        length = len(users)
        ids = list(range(length))
        random.shuffle(ids)
        ids1 = ids[:int(length/6)]
        ids2 = ids[int(length/6):int(length*4/6)]
        ids3 = ids[int(length*4/6):]

        counter = 0
        while counter < amt:
            counter +=1
            tradeId = str(random.randint(13676736367,93938398938938))
            buyerId = random.randint(0, length)
            sellerId = random.randint(0,length)
            while buyerId == sellerId:
                sellerId = random.randint(0,length)
            amount = random.randint(150, 10000)
            curr = random.randint(1,3)
            if curr == 2:
                rates = random.uniform(7.45,7.55)
            else:
                rates = random.uniform(1.05, 1.15)
            if sellerId in ids1:
                max_time = 400
            elif sellerId in ids2:
                max_time = 700
            else:
                max_time = 1050
            if floor == True:
                timeToProcess = random.randint(100,2000)
            else:
                timeToProcess = random.randint(300, max_time)
            buyerRating = float((2000 - timeToProcess - random.randint(0,100))/160)
            if buyerRating < 3:
                buyerRating = float(3.0)
            sellerRating = buyerRating + random.uniform(-1.0, 1.0)
            if sellerRating > 10.0:
                sellerRating = 10.0
            if buyerRating > 10.0:
                buyerRating = 10.0

            Trade.objects.create(tradeId = tradeId, buyerId = str(buyerId), sellerId=str(sellerId),
                                amount = str(amount), currency = str(curr), successful = True, buyerRating = str(buyerRating),
                                sellerRating = str(sellerRating), timeToProcess = str(timeToProcess), rates = str(rates))


    def generate_all_cus():
        cuss = Customer.objects.all()
        for cus in cuss:
            buyTrades = Trade.objects.filter(buyerId = cus.id)
            sellTrades = Trade.objects.filter(sellerId = cus.id)
            
            # get avg rating
            sellAvg = 0
            for _  in sellTrades:
                sellAvg += float(_.buyerRating)
            buyAvg = 0
            for _  in buyTrades:
                buyAvg += float(_.sellerRating)
            try:
                avg = float((sellAvg+buyAvg)/(len(sellTrades)+len(buyTrades)))
            except ZeroDivisionError:
                avg = float(0.0)
            
            cus.ratings = avg
            # get trade count
            cus.trades = len(buyTrades) + len(sellTrades)
            
            # get avg processing time
            avgPT = 0
            for _ in sellTrades:
                avgPT += int(_.timeToProcess)
            try:
                avgPT = avgPT/len(sellTrades)
            except ZeroDivisionError:
                avgPT = 0
            cus.processingTime = avgPT
            cus.save()

    def delete_all():
        trades = Trade.objects.all()
        for _ in trades:
            _.delete()
    
    data = CustomerSerializer(Customer.objects.all().order_by("-ratings"), many = True).data

    return Response({"msg":data}, status = 200)

@api_view(['GET'])
def create_ads(request):
    cuss = Customer.objects.all()
    def createAds():
        for cus in cuss:
            ad_count = random.randint(1,3)
            adId = [1, 2, 3]
            random.shuffle(adId)
            for curr in adId[:ad_count]:
                if cus.ratings > 8.5:
                    min_amount = random.randint(10,30) * 100
                    max_amount = random.randint(50,99) * 100
                elif cus.ratings < 8.0:
                    min_amount = random.randint(15,20) * 10
                    max_amount = random.randint(10,99) * 100
                else:
                    min_amount = random.randint(15,20) * 10
                    max_amount = random.randint(10,66) * 100
                if curr == 2:
                    if cus.ratings > 8.8:
                        rates = random.uniform(7.45,7.50)
                    else:     
                        rates = random.uniform(7.45, 7.55)
                else:
                    if cus.ratings > 8.8:
                        rates = random.uniform(1.05,1.10)
                    else:
                        rates = random.uniform(1.05,1.15)
                Ad.objects.create(customer = cus, currency = str(curr),min_amount = min_amount, max_amount = max_amount, rates = rates )
    
    def delete_duplicates():
        cuss = Customer.objects.all()
        def delete_duplicate_for_ad(_ads):
            ad_len = len(_ads)
            if  ad_len > 1:
                for ad in range(0, ad_len - 1):
                    _ads[ad].delete()


        for cus in cuss:
            ads1 = Ad.objects.filter(customer = cus, currency = "0")
            ads2 = Ad.objects.filter(customer = cus, currency = "1")
            ads3 = Ad.objects.filter(customer = cus, currency = "2")
            
            for itm in [ads1, ads2, ads3]:
                delete_duplicate_for_ad(itm)
    
    def delete_all_ads():
        ads = Ad.objects.all()
        for ad in ads:
            ad.delete()

    def addID():
        ads = Ad.objects.all()
        for ad in ads:

            ad.adId = f"{ad.customer.user.username}-{random.randint(1000000000000, 99999999999999)}"
            ad.save()
    
    ads = AdSerializer(Ad.objects.all(), many=True).data
    return Response({'data': ads},status = 200)

@api_view(['GET'])
def getAds(request):
    # auth
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
        customer = Customer.objects.get(user = user)
    except Token.DoesNotExist:
        return Response({"msg":"Your session has expired, sign in again to continue."}, status = 301)
    # serailize ad data excluding user own ads
    ads = Ad.objects.filter(is_active = True).exclude(customer = customer)
    data = AdSerializer(ads, many=True).data
    for _ in data:
        if _['currency'] == "2":
            _['rate_floor'] = _['rates']/7.55
        else:
            _['rate_floor'] = _['rates']/1.15

        cus = Customer.objects.get(id = _['customer'])
        _['customer'] = CustomerSerializer(cus).data
        _['customer']['user'] = cus.user.username
    # sort by user rating
    data = sorted(data, key = lambda x: x['customer']['ratings'], reverse = True)
    
    context = {'ads':data}
    return Response(context, status = 200)

@api_view(['GET'])
def fetch_trades(request):
    print("here")
    try:
        user = Token.objects.get(key = str(request.headers['Authorization'])).user
    except:
        return Response({"msg":'Your session has expired. Sign in again to continue.'}, status = 301)

    cus = Customer.objects.get(user = user)
    trades = Trade.objects.filter(Q(buyerId = str(cus.id))|Q(sellerId = str(cus.id))).order_by("-time")
    for trade in trades:
        check_trade_viability(trade)
    trades = TradeSerializer(trades, many = True).data
    for trade in trades:
        trade['buyerId'] = Customer.objects.get(id = int(trade['buyerId'])).user.username
        trade['sellerId'] = Customer.objects.get(id = int(trade['sellerId'])).user.username
    context = {'trades':trades}
    return Response(context,status = 200)


@api_view(["GET", "POST"])
def verify(request):
    if request.method == "POST":
        try:
            cus = Customer.objects.get(vcode = request.data['otp'])
            cus.emailVerified = True
            cus.save()
            cus_data = CustomerSerializer(cus).data
            token, created = Token.objects.get_or_create(user = cus.user)
            return Response({'user': cus_data, 'key' : token.key}, status = 200)
        except:
            return Response({'msg':"Verification failed."}, status = 400)
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
        otp = ""
        for i in range(0,32):
            otp += random.choice(string.ascii_letters)
        customer = Customer.objects.get(user = user)
        customer.vcode = otp
        customer.save()
    except Token.DoesNotExist:
        return Response({'msg':"Your session has expired. Sign in again to continue."}, status = 403)
    return Response({'msg' : otp}, status = 200)


@api_view(["POST"])
def verify_id(request):
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
        customer = Customer.objects.get(user = user)
        ver_type = request.data['verType']
        
        if customer.idDocs and ver_type=="idDocs":
            return Response({"idDocs":customer.idDocs.url},status = 200)
        if customer.selfie and ver_type == "selfie":
            return Response({'selfie' : customer.selfie.url}, status = 200)
        base64_img = request.data['image']
        if base64_img.startswith("data:image"):
            base64_img = base64_img.split(",")[1]
        image = ContentFile(base64.b64decode(base64_img), name = f"{user.username.lower()}{ver_type.lower()}{random.randint(10000,9000000)}.jpg")
        if ver_type == "idDocs":
            customer.idDocs = image
        elif ver_type == "selfie":
            customer.selfie = image
        customer.save()
        if customer.idDocs:
            id_docs_url = customer.idDocs.url
        else:
            id_docs_url = None

        if customer.selfie:
            selfie_url = customer.selfie.url
        else:
            selfie_url = None

        return Response({"idDocs" : id_docs_url , "selfie":selfie_url } ,status = 200)
    except Token.DoesNotExist:
        return Response(status = 204)

@api_view(['POST'])
def init_new_trade(request):



    user =  Token.objects.get(key =  request.headers['Authorization']).user # validate user
    customer = Customer.objects.get(user = user)
    # extract data
    ad = Ad.objects.get(adId = str(request.data['adId']))


    bank_name = str(request.data['bankName'])
    account_number = str(request.data['accountNumber'])
    receiver_name = str(request.data['receiverName'])
    remark = str(request.data['remark'])
    amount = str(request.data['amount'])

    # validate data
    if len(bank_name) < 1:
        return Response({"msg":"Bank Name cannot be blank."}, status = 400)
    if len(receiver_name) < 1:
        return Response({"msg":"Receiver's Name cannot be blank."}, status = 400)
    try:
        account_number = int(account_number)
    except:
        return Response({"msg":"Invalid account number format."}, status = 400)
    try:
        amount = amount.replace(",","")
        amount = float(amount)
    except ValueError:
        return Response({"msg":"Please enter the amount using numbers only. Do not include symbols, spaces, or any non-numeric characters."}, status = 400)
    if(len(remark) < 1):
        remark = None

    # create trade
    if(customer.balance < amount):
        return Response({"msg":"Insufficient Funds."}, status = 400)
    if(amount < ad.min_amount or amount > ad.max_amount):
        return Response({"msg":f"Ensure trade must be between ${ad.min_amount} to ${ad.max_amount}"}, status = 400)

    tradeId = str(random.randint(100000000000000, 99999999999999999))

    trade = Trade.objects.create(tradeId = tradeId, buyerId = str(customer.id), sellerId = ad.customer.id, amount = str(amount), rates = ad.rates, currency = ad.currency, bank_name = bank_name, receiver_name = receiver_name, account_number = account_number, remark = remark )
    customer.balance = customer.balance - amount
    customer.save()
    trade_data = TradeSerializer(trade).data
    context={'cus_bal' : customer.balance, 'trade_id' : trade.tradeId}
    return Response(context, status = 200)


@api_view(['POST'])
def init_new_qr_trade(request):
    # validate user
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
        customer = Customer.objects.get(user = user)
    except Token.DoesNotExist:
        return Response({"msg":"Your session has expired."}, status = 301)
    
    # validate amount
    try:
        amount = str(request.data['amount'])
        amount = float(amount.replace(",",""))
    except ValueError:
        return Response({'msg':"Trade amount must be valid numerical value."}, status = 400)
    
    bank_name = str(request.data['bankName'])
    if len(bank_name) == 0:
        return Response({'msg':"Enter a valid institution name to proceed with your payment."}, status = 400)

    tradeId = str(random.randint(100000000000000, 99999999999999999))
    image = str(request.data['image'])
    if not image:
        return Response({'msg':"Invalid Qr code."}, status = 400)
    if image.startswith("data:image"):
        image = image.split(",")[1]
    qr_code = ContentFile(base64.b64decode(image), name= f"QRCode{tradeId}.jpg")
    
    ad_id = str(request.data['adId'])
    ad = Ad.objects.get(adId = ad_id)

    # create trade
    if(customer.balance < amount):
        return Response({"msg":"Insufficient Funds."}, status = 400)
    if(amount < ad.min_amount or amount > ad.max_amount):
        return Response({"msg":f"Ensure trade must is between ${ad.min_amount} to ${ad.max_amount}"}, status = 400)

    trade = Trade.objects.create(tradeId = tradeId, buyerId = str(customer.id), sellerId = ad.customer.id, amount = str(amount), rates = ad.rates, currency = ad.currency, bank_name = bank_name,qr_code=qr_code)
    customer.balance = customer.balance - amount
    customer.save()
    trade_data = TradeSerializer(trade).data
    context={'cus_bal' : customer.balance, 'trade_id' : trade.tradeId}
    return Response(context, status = 200)

        

    


@api_view(['GET','POST'])
def trade(request, trade_id):
    # get user
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
    except Token.DoesNotExist:
        return Response({'msg':"Your session has expired. Sign in again to continue"}, status =403)
    # get customer for this user
    cus = Customer.objects.get(user = user)
    # get trade
    try:
        trade = Trade.objects.get(tradeId = trade_id)
    except Trade.DoesNotExist:
        return Response({'msg':"Trade not found"}, status =400)
    
    # generate trade data
    trade_data = gen_trade_data(cus, trade)
    if trade_data == None:
        return Response({'msg':"Trade not found"}, status =400)

    # get templates
    if cus.id == int(trade.buyerId):
        other_email = Customer.objects.get(id = int(trade.sellerId)).email
        templates = TemplateMessageSerializer(TemplateMessage.objects.filter(Q(for_buyer = True)|Q(for_buyer = None)).order_by("?"), many=True).data
    else:
        other_email = Customer.objects.get(id = int(trade.buyerId)).email
        templates = TemplateMessageSerializer(TemplateMessage.objects.filter(Q(for_buyer = False)|Q(for_buyer = None)).order_by("?"), many=True).data
    
    #get messages
    messages = TradeMessageSerializer(TradeMessage.objects.filter(trade = trade).order_by("time"), many = True).data


    for message in messages:
        message['sender'] = Customer.objects.get(id = message['sender']).user.username
    trade_data['other_email'] = other_email
    return Response({"trade_data" : trade_data, "templates" : templates, "messages" : messages}, status = 200)


@api_view(['POST'])
def rate_transaction(request):
    user = Token.objects.get(key = request.headers['Authorization']).user
    cus = Customer.objects.get(user = user)
    rating = request.data['rating']
    tradeId = str(request.data['tradeId'])
    trade = Trade.objects.get(tradeId = tradeId)
    if cus.id == int(trade.buyerId) and trade.sellerRating == None:
        
        trade.sellerRating = str(rating)
    elif cus.id == int(trade.sellerId) and trade.buyerRating == None:
        trade.buyerRating = str(rating)
    trade.save()
    context = {"seller_rating":trade.sellerRating, "buyerRating":trade.buyerRating}
    return Response(context, status = 200)

@api_view(['GET'])
def get_cus_ads(request):

    # fetch user data
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
    except Token.DoesNotExist:
        return Response({"msg":"Your session has expiried. Sign in again to continue"}, status = 400)
    customer = Customer.objects.get(user = user)
    data = generate_ad_data(customer)
    return Response({"msg":data}, status = 200)

@api_view(['POST'])
def delete_ad(request):

    user = Token.objects.get(key = request.headers['Authorization']).user
    customer = Customer.objects.get(user = user)
    ad = Ad.objects.get(adId = str(request.data['adId']))
    if ad.customer != customer:
        return Response({"msg":"Not Found"}, status = 404)
    if ad.is_active:
        ad.is_active = False
        ad.save()
    else:
        ad.delete()
    
    data = generate_ad_data(customer)
    return Response({'msg':data}, status = 200)


@api_view(['POST'])
def create_new_ad(request):
    # get user details
    user = Token.objects.get(key = request.headers['Authorization']).user
    customer = Customer.objects.get(user = user)
    print(request.data)
    # ruun validator
    validated_input = validate_ad_input(request.data)
    # if not valid, break
    if not validated_input['status']:
        return Response({"msg":validated_input['msg']}, status = 400)
    # filter if ad of same type already exists
    curr_ads = Ad.objects.filter(customer = customer, currency = validated_input['data']['currency'], is_active = True)
    if curr_ads:
        if validated_input['data']['currency'] == "1":
            ad_curr = "USD"
        elif validated_input['data']['currency'] == "2":
            ad_curr = "CNY"
        elif validated_input['data']['currency'] == "3":
            ad_curr = "EUR"
        return Response({"msg":f"Archive your current {ad_curr} ad to continue."}, status = 400)
    
    methods = request.data['paymentMethods']
    # create ad
    ad_id = f'{customer.user.username}-{random.randint(100000000, 99999999999999)}'
    Ad.objects.create(adId = ad_id, customer =customer, currency = validated_input['data']['currency'],
        min_amount=validated_input['data']['min'], max_amount = validated_input['data']['max'], rates = validated_input['data']['rates'],
        bank = methods['bank'], alipay = methods['alipay'],wechatpay = methods['wechatpay'],paypal = methods['paypal'],wise = methods['wise'],
        sepa = methods['sepa'],revolut = methods['revolut'],swift = methods['swift'],payoneer = methods['payoneer'],remitly = methods['remitly'], terms = validated_input['data']['terms'])
        
    data = generate_ad_data(customer)
    return Response({"data":data},status = 200)


@api_view(['GET'])
def get_faqs(request):
    faqs = FaqSerializer(Faq.objects.all(), many=True).data
    return Response({"faqs":faqs}, status = 200)


@api_view(['GET'])
def get_wallet_address(request):
    wallet = Wallet.objects.first()
    return Response({'address':wallet.wallet_address}, status = 200)

@api_view(['POST', "GET"])
def handle_transaction(request, transaction_type):
    try:
        user = Token.objects.get(key = request.headers['Authorization']).user
        customer = Customer.objects.get(user = user)
    except Token.DoesNotExist:
        return Response({'msg':"Your Session has expired. Sign in again to continue"}, status = 301)
    if transaction_type == "deposit":
        address = str(request.data['address'])
        possible = TransactionRequest.objects.filter(customer = customer, transaction_address = address, is_deposit = True)
        if len(possible) != 0:
            return Response({'msg':"Duplicate Transaction"}, status = 400)
        transaction_id = f'{customer.user.username}{random.randint(100000000000,900000000000)}'       
        trans = TransactionRequest.objects.create(transaction_id = transaction_id, customer = customer, transaction_address = address, is_deposit = True)
        trans_data = TransactionRequestSerializer(trans).data
        return Response({"msg":trans_data}, status = 200)
    elif transaction_type =="history":
        history = TransactionRequestSerializer(TransactionRequest.objects.filter(customer = customer).order_by("-time"), many = True).data
        return Response({'msg':history}, status = 200)
    elif transaction_type == "withdrawal":
        address = str(request.data['wallet'])
        if address == "":
            return Response({'msg':"Provide a valid wallet address."}, status = 400)
        try:
            amount = str(request.data['amount'])
            sub = str(request.data['sub'])
            amount = float(str(amount)+'.'+ sub)
            if customer.balance < amount:
                return Response({'msg':"Insufficient Funds"}, status = 400)
        except ValueError:
            return Response({'msg':"Enter a valid numeric amount."}, status = 400)
        transaction_id = f'{customer.user.username}{random.randint(100000000000,900000000000)}'       
        customer.balance -= amount
        customer.save()
        trans = TransactionRequest.objects.create(transaction_id = transaction_id, customer = customer, transaction_address = address, is_deposit = False, amount = amount)
        trans_data = TransactionRequestSerializer(trans).data
        return Response({"msg":trans_data, "bal":customer.balance}, status = 200)
    else:
        return Response({'msg':"An unexpected error has occured."}, status = 400)

@api_view(['POST'])
def reactivate_ad(request):
    try:
        user = Token.objects.get(key = str(request.headers['Authorization'])).user
        customer = Customer.objects.get(user = user)
    except Token.DoesNotExist:
        return Response({'msg':"Your session has expired. Sign in again to continue."}, status = 301)
    
    try:
        ad = Ad.objects.get(adId = str(request.data['adId']))
    except Ad.DoesNotExist:
        return Response({'msg':"Ad does not exist."}, status = 400)
    
    active_ads = Ad.objects.filter(customer = customer, is_active = True)
    for active_ad in active_ads:
        if ad.currency == active_ad.currency:        
            if ad.currency == "1":
                ad_curr = "USD"
            elif ad.currency == "2":
                ad_curr = "CNY"
            elif ad.currency == "3":
                ad_curr = "EUR"
            return Response({'msg':f"Archive your current {ad_curr} ad to continue."}, status = 400)

    ad.is_active = True
    ad.save()
    ads = generate_ad_data(customer)
    return Response({'ads':ads}, status = 200)


@api_view(['POST'])
def reset_password(request):
    # extrct clean data
    user_id = str(request.data['userId'])
    # get possible user
    try:
        user = User.objects.get(username = user_id)
        customer = Customer.objects.get(user = user)
    except User.DoesNotExist:
        try:
            customer = Customer.objects.get(email = user_id)
        except Customer.DoesNotExist:
            return Response({"msg":"User does not exist."}, status = 400)
    # generate otp and dd to user in db
    otp = ""
    for i in range(0,32):
        otp += random.choice(string.ascii_letters)
    customer.vcode = otp
    customer.save()

    context = {'msg':otp, "email":customer.email, 'username':customer.user.username}
    return Response(context, status = 200)


@api_view(['GET','POST'])
def new_pass(request, otp):
    # attempt user fetch, alert on fail
    try:
        cus = Customer.objects.get(vcode = otp)
    except:
        return Response({'msg':"Invalid code"}, status = 200)
    # if get, send username for aesthetics
    if request.method == "GET":
        return Response({'username':cus.user.username}, status = 200)
    # if post
    if request.method == "POST":
        # validate
        pass1 = str(request.data['pass1'])
        pass2 = str(request.data['pass2'])
        # password mismatch
        if pass1 != pass2:
            return Response({'msg':"Your passwords do not match"}, status = 400)
        
        if len(pass1) < 8:
            return Response({'msg':"Your passwords must be at least 10 characters."}, status = 400)
    
        # set new password
        cus.user.set_password(pass1)
        cus.user.save()
        # serialize user
        data = gen_cus_data(cus.user)
        # delete all sessions and create a new one
        tokens = Token.objects.filter(user = cus.user)
        for token in tokens:
            token.delete()
        new_token = Token.objects.create(user = cus.user)
        # send new data
        return Response({'user':data, "key": new_token.key}, status = 200)
        

@api_view(['GET'])
def socket_validate_user(request, trade_id):
    print(request.headers['Authorization'])
    user = Token.objects.get(key = request.headers['Authorization']).user
    try:
        trade = Trade.objects.get(tradeId = trade_id)
    except Trade.DoesNotExist:
        return Response({"msg":False}, status = 400)
        

    cus = Customer.objects.get(user = user)
    if cus.id != int(trade.buyerId) and cus.id != int(trade.sellerId):
        return Response({"msg":False}, status = 400)
    else:
        return Response({"msg":True}, status = 200)


@api_view(['POST'])
def create_new_message(request):
    
    data = json.loads(request.body)
    trade_id = data['trade_id']
    message_text = data['text']
    cookie = request.headers['Authorization']
    
    trade = Trade.objects.get(tradeId = trade_id)
    cus = Customer.objects.get(user = Token.objects.get(key = cookie).user)
    
    if int(trade.buyerId) == cus.id or int(trade.sellerId) == cus.id:
    
        new_message = TradeMessage.objects.create(trade = trade, message_text = message_text, sender = cus)
        new_message_data = TradeMessageSerializer(new_message).data
        new_message_data['sender']= cus.user.username    
        return Response({"msg":new_message_data}, status = 200)
    
@api_view(['POST'])
def socket_append_receipt(request):
    customer = Customer.objects.get(user = Token.objects.get(key = request.headers['Authorization']).user)
    data = json.loads(request.body)
    trade = Trade.objects.get(tradeId = data['trade_id'])
    b64img = data['image']

    if int(trade.buyerId) == customer.id or int(trade.sellerId) == customer.id:
        image = ContentFile(base64.b64decode(b64img), name =f"TradeReceipt{data['trade_id']}.jpg")
        trade.receipt = image
        trade.save()
        return Response({'msg':trade.receipt.url}, status = 200)


@api_view(['POST'])
def socket_release_usdt(request):
    customer = Customer.objects.get(user = Token.objects.get(key = request.headers['Authorization']).user)
    data = json.loads(request.body)
    trade = Trade.objects.get(tradeId = data['trade_id'])
    seller = Customer.objects.get(id = int(trade.sellerId))
    if customer.id == int(trade.buyerId) and trade.successful != True:
        seller.balance += float(trade.amount)
        trade.successful = True
        trade.timeToProcess = int((timezone.now() - trade.time).total_seconds())
        seller.save()
        trade.save()
        context= {"time_to_process" : trade.timeToProcess}
        return Response({'msg':context}, status = 200)


@api_view(['GET'])
def socket_get_dispute_data(request, trade_id):
    
    try:
        customer = Customer.objects.get(user = Token.objects.get(key = request.headers['Authorization']).user)
        trade = Trade.objects.get(tradeId = trade_id)

        if int(trade.buyerId) != customer.id and int(trade.sellerId) != customer.id:
            return Response({'msg':False}, status = 400)
        else:
            trade_data = TradeSerializer(trade).data
            buyer = Customer.objects.get(id = int(trade_data['buyerId']))
            seller =Customer.objects.get(id = int(trade_data['sellerId']))
            
            dispute_messages = DisputeMessageSerializer(DisputeMessage.objects.filter(
                trade = trade), many = True).data
            for message in dispute_messages:
                if int(message['sender']) == buyer.id:
                    message['sender'] = buyer.user.username
                
                elif int(message['sender']) == seller.id:
                    message['sender'] = seller.user.username
            
            msg = {"trade data" : trade_data, "messages" : dispute_messages}
            return Response({"msg":msg}, status = 200)
    except Token.DoesNotExist:
        return Response({"msg":False}, status = 400)

    

@api_view(['POST'])
def create_new_dispute_message(request):
    customer = Customer.objects.get(user = Token.objects.get(key = request.headers['Authorization']).user)
    data = json.loads(request.body)
    trade = Trade.objects.get(tradeId = data['trade_id'])
    event = data['data']

    if(event['img'] == None):
        image = None
    else:
        img = event['img']
        if img.startswith("data:image"):
            img = img.split(",")[1]
        random_num = random.randint(10000, 9999999)
        image = ContentFile(base64.b64decode(img), name = f"dispute{random_num}.jpg")
    message = DisputeMessage.objects.create(text=event['text'], image = image, trade = trade, sender = customer, msg_id = event['msg_id'])
    message_data = DisputeMessageSerializer(message).data
    message_data['sender'] = customer.user.username
    return Response({'msg':message_data}, status = 200)
