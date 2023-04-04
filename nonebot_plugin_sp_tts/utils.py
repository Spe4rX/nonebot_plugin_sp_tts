import time
import json
import nls
import os

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from nonebot.log import logger

URL = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
# 参考https://help.aliyun.com/document_detail/450255.html获取token
# 获取Appkey请前往控制台：https://nls-portal.console.aliyun.com/applist


class Token:
    def __init__(self):
        self.cfg_path = 'data/tts/'
        self.cfg_name = 'token_cfg.json'
        self.ReadCfg()

    def ReadCfg(self):
        try:
            with open(self.cfg_path+self.cfg_name, 'r', encoding='utf-8') as f:
                self.cfg = json.loads(f.read())
            return self.cfg
        except Exception as e:
            logger.warning(f'创建{self.cfg_path}{self.cfg_name}')
            self.cfg = {
                "setKeySecret": "",
                "setAccessKeyId": "",
                "token": "",
                "expireTime": 0,
            }
            self.WriteCfg()

    def WriteCfg(self):
        os.makedirs(self.cfg_path, mode=0o777, exist_ok=True)
        with open(self.cfg_path+self.cfg_name, 'w', encoding='utf-8') as f:
            print(self.cfg)
            f.write(json.dumps(self.cfg))

    def UpdateToke(self):
        client = AcsClient(
            self.cfg["setKeySecret"],
            self.cfg["setAccessKeyId"],
            "cn-shanghai")
        request = CommonRequest()
        request.set_method('POST')
        request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
        request.set_version('2019-02-28')
        request.set_action_name('CreateToken')
        try:
            response = client.do_action_with_exception(request)
            jss = json.loads(response)
            if 'Token' in jss and 'Id' in jss['Token']:
                token = jss['Token']['Id']
                expireTime = jss['Token']['ExpireTime']
        except Exception as e:
            print(e)
            return
        self.cfg["token"] = token
        self.cfg["expireTime"] = int(expireTime)
        self.WriteCfg()

    def GetToken(self):
        if time.time() > self.cfg["expireTime"]:
            logger.debug(
                f'当前时间：{time.time()},token过期时间:{self.cfg["expireTime"]},重新获取Token')
            self.UpdateToke()
        return self.cfg["token"]


class Tts:
    def __init__(self, audiofile):
        self.token = Token()
        self.cfg_path = 'data/tts/'
        self.cfg_name = 'cfg.json'
        self.ReadCfg()
        self.audiofile = audiofile
        self.ttsstatus = 0
        self.ttsstatusmessage = ""

    def start(self, text, moduelName):
        self.moduelName = moduelName
        self.ttsstatus = 0
        self.ttsstatusmessage = ""
        self.__text = text
        self.__f = open(self.audiofile, "wb")
        tts = nls.NlsSpeechSynthesizer(
            url=URL,
            token=self.token.GetToken(),
            appkey=self.cfg["appkey"],
            on_metainfo=self.test_on_metainfo,
            on_data=self.test_on_data,
            on_completed=self.test_on_completed,
            on_error=self.test_on_error,
            on_close=self.test_on_close)
        r = tts.start(self.__text,
                      voice=self.cfg["moduel"][self.moduelName],
                      aformat="mp3")
        print(f"tts done with result:{r}")

    def test_on_metainfo(self, message, *args):
        logger.debug(f"on_metainfo message=>{message}")

    def test_on_error(self, message, *args):
        logger.debug(f"on_error args=>{args}")

    def test_on_close(self, *args):
        logger.debug(f"on_close: args=>{args}")
        try:
            self.__f.close()
        except Exception as e:
            logger.debug(f"close file failed since:{e}")

    def test_on_data(self, data, *args):
        try:
            self.__f.write(data)
        except Exception as e:
            logger.debug(f"write data failed:{e}")

    def test_on_completed(self, message, *args):
        logger.debug(f"on_completed:args=>{args} message=>{message}")
        j = json.loads(message)
        self.ttsstatus = j['header']['status']
        self.ttsstatusmessage = j['header']['status_text']

    def ReadCfg(self):
        try:
            with open(self.cfg_path+self.cfg_name, 'r', encoding='utf-8') as f:
                self.cfg = json.loads(f.read())
        except Exception as e:
            logger.warning(f'创建{self.cfg_path}{self.cfg_name}')
            self.cfg = {"appkey": "", "moduel": {}}
            self.WriteCfg()

    def WriteCfg(self):
        os.makedirs(self.cfg_path, mode=0o777, exist_ok=True)
        with open(self.cfg_path+self.cfg_name, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.cfg))

    def CheckModule(self, moduleName):
        return moduleName in self.cfg["moduel"]
