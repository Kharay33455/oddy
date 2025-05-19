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
import re, random, string, base64


def gen_cus_data(_user):
    cus_data = CustomerSerializer(Customer.objects.get(user = _user)).data
    cus_data['user'] = _user.username
    
    return cus_data

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def validate(_str, _acceptables):
    for _ in _str:
        if _ not in _acceptables:
            return False
    return True


# Create your views here.

@api_view(['POST'])
def login_request(request):
    username = str(request.data['username']).strip()
    password = str(request.data['password']).strip()
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
    ads = Ad.objects.all()
    data = AdSerializer(ads, many=True).data
    for _ in data:
        if _['currency'] == "2":
            _['rate_floor'] = _['rates']/7.55
        else:
            _['rate_floor'] = _['rates']/1.15

        cus = Customer.objects.get(id = _['customer'])
        _['customer'] = CustomerSerializer(cus).data
        _['customer']['user'] = cus.user.username
    data = sorted(data, key = lambda x: x['customer']['ratings'], reverse = True)
    context = {'ads':data}
    return Response(context, status = 200)

@api_view(['GET'])
def fetch_trades(request):
    user = Token.objects.get(key = str(request.headers['Authorization'])).user
    cus = Customer.objects.get(user = user)
    trades = Trade.objects.filter(Q(buyerId = str(cus.id))|Q(sellerId = str(cus.id))).order_by("time")
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