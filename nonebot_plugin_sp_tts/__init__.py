import aiohttp
import asyncio
import nonebot
import os
from nonebot import get_driver
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.typing import T_State
from .utils import *
from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

current_path = os.path.abspath(os.path.dirname(
    os.path.abspath(__file__)) + os.path.sep + ".") + "/"
fileName = "tts.mp3"
filePath = current_path+fileName

occupied = False

tts = Tts(filePath)

chat = on_regex(r"^/(tts|文字转语音)\s?(\S*)\s([\s\S]*)", priority=5)

@chat.handle()
async def _(state: T_State):
    global occupied
    if occupied:
        await chat.finish("Occupied")

    occupied = True
    args = list(state["_matched_groups"])

    moduleName = args[1]
    if not moduleName:
        moduleName = "sk"

    if not tts.CheckModule(moduleName):
        occupied=False
        await chat.finish("没有找到声音模型")

    t = args[2]
    if t == "" or t == None or t.isspace():
        occupied=False
        await chat.finish("无内容")

    # await chat.send("生成中")

    tts.start(t, moduleName)
    if tts.ttsstatus == 20000000:
        await chat.send(MessageSegment.record(f"file:///{filePath}"))
    else:
        await chat.send(tts.ttsstatusmessage)

    occupied = False
