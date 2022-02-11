import pytest
import os
from telethon.sessions import StringSession
from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message


api_id = _
api_hash = '_'


@mark.asyncio
async def test_start():
    # Create a conversation
    client = TelegramClient(
        'test', api_id, api_hash,
        sequential_updates=True
    )
    await client.start()
    await client.connect()
    async with client.conversation("@Ambrozi_bot", timeout=5) as conv:
        await conv.send_message("/start")
        resp: Message = await conv.get_response()
        assert "Привет WorthIt. Отправь номер твоей группы" in resp.raw_text

        await conv.send_message("213")
        resp: Message = await conv.get_response()
        assert "Не могу найти эту группу ☹" in resp.raw_text

        await conv.send_message("19701.1")
        resp: Message = await conv.get_response()
        assert "Твоя группа – 19701.1. Теперь нажми на кнопку ниже 🔽" in resp.raw_text

        await client.disconnect()

@mark.asyncio
async def test_review():
    client = TelegramClient(
        'test', api_id, api_hash,
        sequential_updates=True
    )
    await client.start()
    await client.connect()
    async with client.conversation("@Ambrozi_bot", timeout=5) as conv:
        await conv.send_message("Отзывы")
        resp: Message = await conv.get_response()
        assert "Введите фамилию преподавателя" in resp.raw_text

        await conv.send_message("Пупкин")
        resp: Message = await conv.get_response()
        assert "Не удалось найти преподавателя с такой фамилией" in resp.raw_text

        await conv.send_message("Петров")
        resp: Message = await conv.get_response()
        assert resp.button_count == 2
        assert resp.buttons[0][0].text == "Петров Владимир Валерьевич"
        assert resp.buttons[1][0].text == "Петров Евгений Сергеевич"

        callback = await resp.click(text="Петров Владимир Валерьевич")
        resp: Message = await conv.get_response()
        assert 'Петров Владимир Валерьевич\nОтзывов пока нет, оставь первый!' in resp.raw_text



        await client.disconnect()

