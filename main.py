import requests
import string
import random
import time
import uuid
import hashlib
import re

lets = string.ascii_uppercase+string.digits

class Main:
    def __init__(self):
		# Генерируем данные для дальнейшего использования
        self.device_id = str(uuid.uuid4())
        self.device_model = 'SM-'+''.join([random.choice(lets) for i in range(6)])
        self.rand_sys_id = "".join([random.choice(lets) for i in range(6)])
        self.android_ver = f'{random.randint(4,10)}.0'
        self.rand_user_id = random.randint(10000000,40000000)
        self.device_software = f'Android {self.android_ver} {self.rand_sys_id} se.infra DID[{self.device_id}|{self.rand_user_id}|{self.device_id}]'
        self.mac = ':'.join([''.join([random.choice('abcdef0123456789') for i in range(2)]) for i in range(6)])
        self.user_agent = f'Dalvik/2.1.0 (Linux; U; Android {self.android_ver}; {self.device_model} Build/{self.rand_sys_id })'
        
    def login(self):
        ts = str(int(time.time()*1000))
		# Хэшируем device_secure_id
        self.secure_id = hashlib.sha1(f'client_idandroiddevice_id{self.device_id}device_manufacturersamsungdevice_model{self.device_model}device_software{self.device_software}device_typetabletkeyae307f3f-78ce-4389-8b35-200113d4bf4dmac_address{self.mac}timestamp{ts}'.encode()).hexdigest()
        r = requests.post('https://auth.playfamily.ru/dev_login',
                          allow_redirects=False,
                          verify=False,
                          data={'client_id': 'android',
                                'device_id': self.device_id,
                                'device_manufacturer': 'samsung',
                                'device_model': self.device_model,
                                'device_secure_id': self.secure_id,
                                'device_software': self.device_software,
                                'device_type': 'tablet',
                                'mac_address': self.mac,
                                'redirect_uri': 'http://androidyotavideo',
                                'timestamp': ts})
        self.token_code = re.search('code=(.*?)&', r.headers['Location']).group(1) # Парсим токен
        ts = str(int(time.time()*1000))
		# Генерим сигнатуру основа которой это timestamp и параметры запроса (дальше сигнатура запросов аналогично генерится)
        raw_sig = f'27051703{ts}deviceExtras{{"supportedDrm":"","mobileNetworkCodes":"20","supportHd":false,"appVersion":"7.10.10","supportFullHd":false,"sdkVersion":22,"supportMultiAudio":true,"supportMultiSubscriptions":true,"drmSoftware":"","supportFeaturedSubscriptions":true}}deviceId{self.device_id}deviceManufacturersamsungdeviceModel{self.device_model}deviceSoftware{self.device_software}deviceTypeTBLtoken{self.token_code}tokenTypeTEMP'
        sig = hashlib.md5(raw_sig.encode()).hexdigest()
        print(raw_sig)
        print(sig)
        r = requests.post('https://ctx.playfamily.ru/screenapi/v1/login/android/2',
                          verify=False,
                          params={'deviceExtras': '{"supportedDrm":"","mobileNetworkCodes":"20","supportHd":false,"appVersion":"7.10.10","supportFullHd":false,"sdkVersion":22,"supportMultiAudio":true,"supportMultiSubscriptions":true,"drmSoftware":"","supportFeaturedSubscriptions":true}',
                                  'deviceId': self.device_id,
                                  'deviceManufacturer': 'samsung',
                                  'deviceModel': self.device_model,
                                  'deviceSoftware': self.device_software,
                                  'deviceType': 'TBL',
                                  'token': self.token_code,
                                  'tokenType': 'TEMP'},
                          headers={'User-Agent': 'Okko Android client',
                                   'X-SCRAPI-SIGNATURE': sig,
                                   'X-SCRAPI-CLIENT-TS': ts,
                                   'Accept-Encoding': 'gzip, deflate'})
        data = r.json()
		# Парсим данные чтобы перенести на них профиль от нашего аккаунта
		# Логика у приложения такая, что нужно создать гостевой профиль чтобы в дальнейшем перенести на него основной
        self.a_key = data['authInfo']['accessKey']
        self.sid = data['authInfo']['sessionToken']
        self.user_id = data['userInfo']['id']
		# Авторизация
        r = requests.post('https://auth.playfamily.ru/play_login',
                          data={'device_type':'tablet',
                                'password':'ianthorpe',
                                'redirect_uri':'http://androidyotavideo',
                                'username':'kamilla_ahmedova@mail.ru'},
                          headers={'User-Agent':self.user_agent,
                                   'Accept-Encoding': 'gzip, deflate'},
                          allow_redirects=False,
                          verify=False)
        print(r.headers)
		# Парсим токен от нашего аккаунта
        self.main_token = re.search('code=(.*?)&', r.headers['Location']).group(1)
        ts = str(int(time.time()*1000))
        raw_sig = f'{self.a_key}{ts}sid{self.sid}token{self.main_token}tokenTypeTEMPuserId{self.user_id}'
        sig = hashlib.md5(raw_sig.encode()).hexdigest()
		# Соединяем гостевой и основной профиль
        r = requests.post('https://ctx.playfamily.ru/screenapi/v1/mergeprofiles/android/2',
                          params={'sid':self.sid,
                                  'token':self.main_token,
                                  'tokenType':'TEMP',
                                  'userId':self.user_id},
                          headers={'User-Agent': 'Okko Android client',
                                   'X-SCRAPI-SIGNATURE': sig,
                                   'X-SCRAPI-CLIENT-TS': ts,
                                   'Accept-Encoding': 'gzip, deflate'},
                          verify=False)
        print(r.json())
        ts = str(int(time.time()*1000))
        raw_sig = f'{self.a_key}{ts}sid{self.sid}userId{self.user_id}'
        sig = hashlib.md5(raw_sig.encode()).hexdigest()
		# Получаем инфу о нашем профиле
        r = requests.get('https://ctx.playfamily.ru/screenapi/v3/profile/android/3',
                         params={'sid':self.sid,
                                 'userId':self.user_id},
                         headers={'User-Agent': 'Okko Android client',
                                   'X-SCRAPI-SIGNATURE': sig,
                                   'X-SCRAPI-CLIENT-TS': ts,
                                   'Accept-Encoding': 'gzip, deflate'},
                         verify=False)
        return r.json()
