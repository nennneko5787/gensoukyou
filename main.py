import discord
from discord import app_commands
from discord.ext import tasks
import os
from collections import defaultdict
import random
import asyncio
import traceback
from keep_alive import keep_alive
import signal
import sys
import g4f
from g4f.client import AsyncClient
from g4f.Provider import GeminiPro
import asyncpg
import aiohttp

chat_rooms = defaultdict(list)

if os.path.isfile(".env"):
    from dotenv import load_dotenv
    load_dotenv(verbose=True)

"""
RetryProvider([
        g4f.Provider.OpenaiChat,
        g4f.Provider.FreeGpt,
    ])
"""

oclient = AsyncClient(
    provider=GeminiPro
)

api_keys = []
proxies = []

# APIキーはここから追加！
# https://aistudio.google.com/app/apikey
for i in range(0, 15):
    if os.getenv(f"gemini{i}") is not None:
        api_keys.append(os.getenv(f"gemini{i}"))

role_info = {
    "": {
        'color': discord.Colour.from_rgb(208, 57, 57),
        "icon": ""
    },
    "博麗霊夢": {
        'color': discord.Colour.from_rgb(208, 57, 57),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000101.png"
    },
    "霧雨魔理沙": {
        'color': discord.Colour.from_rgb(216, 206, 23),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000201.png"
    },
    "フランドール・スカーレット": {
        'color': discord.Colour.from_rgb(232, 177, 119),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th060-070101.png"
    },
    "レミリア・スカーレット": {
        'color': discord.Colour.from_rgb(111, 124, 185),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th060-060101.png"
    },
    "魂魄妖夢": {
        'color': discord.Colour.from_rgb(226, 227, 230),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th070-050101.png"
    },
    "チルノ": {
        'color': discord.Colour.from_rgb(80, 161, 231),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th060-020201.png"
    },
    "ナズーリン": {
        'color': discord.Colour.from_rgb(73, 73, 73),
        "icon": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th120-010101.png"
    },
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def setup_hook():
    await tree.sync()
    icon.start()
    async with aiohttp.ClientSession() as session:
        async with session.get(url="https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text") as response:
            _pros = (await response.text()).replace("\r\n", "\n").replace("\r", "\n").split("\n")
            for _pro in _pros:
                proxies.append(_pro)

@client.event
async def on_ready():
    conn = await asyncpg.connect(os.getenv("dsn"))
    result = await conn.fetch('SELECT * FROM chat_rooms')
    await conn.close()
    for row in result:
        uid = row["id"]
        chat_rooms[uid] = row["data"]
    presence.start()

def get_png_files(directory):
    png_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.png')]
    return png_files

@tasks.loop(minutes=5)
async def icon():
    png_files = get_png_files("./images/")
    selected_file = random.choice(png_files)
    with open(os.path.join("./images/", selected_file), 'rb') as f:
        icon = f.read()
    await client.user.edit(avatar=icon)

@tasks.loop(seconds=20)
async def presence():
    game = discord.Game(f"/init | {len(client.guilds)} servers | {len(chat_rooms)} members are chatting / {len([member for member in client.users if not member.bot])} members")
    await client.change_presence(status=discord.Status.online, activity=game)

def rgb_to_hex(r,g,b):
    return '#{:02x}{:02x}{:02x}'.format(r,g,b)

@tree.command(name="init", description="ボットを使える状態にするために初期化します。新しいキャラクターを使えるようにするためにも使用します。(既存のキャラクター、会話記録は消えません。)")
async def initialize(interaction: discord.Interaction):
    if interaction.guild.me.guild_permissions.manage_roles is not True:
        embed = discord.Embed(
            title="ボットに必要な権限が足りません！",
            description="**以下の権限を付与してください。**\n**ロールの管理** *(MANAGE_ROLES)*",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    log = ""

    for name, data in role_info.items():
        if name == "":
            continue
        role: discord.Role = discord.utils.get(interaction.guild.roles, name=name)
        if not role:
            color_value = data["color"].value  # Get the integer value of the color
            await interaction.guild.create_role(
                name=name,
                color=color_value,
                mentionable=True,
                reason=f"「幻想郷」ボットの初期化により作成されました。"
            )
            log = f"{log}\nロール「{name}」が作成されました。" if log != "" else f"ロール「{name}」が作成されました。"
        else:
            if role.color != data['color']:
                color_value = data["color"].value  # Get the integer value of the color
                await role.edit(color=color_value)
                log = f"{log}\nロール「{name}」の色が「{rgb_to_hex(data['color'].r, data['color'].g, data['color'].b)}」に更新されました。" if log != "" else f"{log}\nロール「{name}」の色が「{rgb_to_hex(data['color'].r, data['color'].g, data['color'].b)}」に更新されました。"

    embed = discord.Embed(
        title="✅初期化に成功しました。",
        description=f"```\n{log}\n```",
        color=discord.Color.green(),
    )
    await interaction.followup.send(embed=embed)

@tree.command(name="chat_clean", description="キャラクターとの会話履歴をリセットし、なかったことにします(???)")
async def chat_clean(interaction: discord.Interaction):
    del chat_rooms[interaction.user.id]
    await interaction.response.send_message("チャット履歴を削除しました。", ephemeral=True)

@tree.command(name="characters", description="キャラクターの一覧を確認できます")
async def characters(interaction: discord.Interaction):
    await interaction.response.defer()
    text = ""
    for name, data in role_info.items():
        if name == "":
            continue
        role: discord.Role = discord.utils.get(interaction.guild.roles, name=name)
        if not role:
            text = f"{text}\n{name} - **/init コマンドを使用して有効化してください**" if text != "" else f"{name} - **/init コマンドを使用して有効化してください**"
        else:
            text = f"{text}\n{role.mention} - **使用可能です**" if text != "" else f"{name} - **/init コマンドを使用して有効化してください**"
    embed = discord.Embed(
        title="キャラクター一覧",
        description=text,
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed)

@tree.command(name="support", description="サポートサーバーの招待リンクを表示します。")
async def chat_clean(interaction: discord.Interaction):
    await interaction.response.send_message("https://discord.gg/D577rtaya5", ephemeral=True)

async def handle_message(message: discord.Message, role_name: str):
    prompt = f"あなたは、幻想郷に住んでいる、{role_name}です。"\
            f"私の名前は{message.author.display_name}です。"\
            f"私はあなたに「{message.clean_content}」と話しました。"\
            f"あなたは{role_name}なので、{role_name}のように出力してください。"\
            "日本語で出力してください。人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
            "返答にはMarkdown記法を使うことができます。"

    async with message.channel.typing():
        try:
            chat_rooms[message.author.id].append(
                {"role": "user", "content": prompt}
            )
            response = await oclient.chat.completions.create(
                model="gemini-1.5-pro-latest",
                api_key=random.choice(api_keys),
                proxy=random.choice(proxies),
                messages=chat_rooms[message.author.id],
            )
            text = response.choices[0].message.content
            chat_rooms[message.author.id].append(
                {"role": "assistant", "content": text}
            )
            
            embed = discord.Embed(title="", description=text, color=role_info[role_name]['color'])
            embed.set_author(name=role_name, icon_url=role_info[role_name]["icon"])
            await message.reply(embed=embed)
        except Exception as e:
            # traceback_info = traceback.format_exc()
            traceback.print_exception(e)
            text = f"どうやら{role_name}の機嫌が悪いらしい...\n```\n{e}\n```"
            embed = discord.Embed(description=text, color=role_info[role_name]['color'])
            embed.set_author(name=role_name, icon_url=role_info[role_name]["icon"])
            await message.reply(text)

async def handle_message_fukusuu(message: discord.Message, role_name: str):
    prompt = f"あなた達は、幻想郷に住んでいる、{role_name}です。"\
            f"私の名前は{message.author.display_name}です。"\
            f"私はあなた達に「{message.clean_content}」と話しました。"\
            f"あなたは{role_name}なので、{role_name}のように出力してください。"\
            "**<人名>**:\n> <内容> という感じに出力してください。"\
            "日本語で出力してください。人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
            "返答にはMarkdown記法を使うことができます。"

    async with message.channel.typing():
        try:
            chat_rooms[message.author.id].append(
                {"role": "user", "content": prompt}
            )
            response = await oclient.chat.completions.create(
                model="gemini-1.5-pro-latest",
                api_key=random.choice(api_keys),
                proxy=random.choice(proxies),
                messages=chat_rooms[message.author.id],
            )
            text = response.choices[0].message.content
            chat_rooms[message.author.id].append(
                {"role": "assistant", "content": text}
            )
            
            embed = discord.Embed(title="", description=text, color=role_info["博麗霊夢"]['color'])
            await message.reply(embed=embed)
        except Exception as e:
            # traceback_info = traceback.format_exc()
            traceback.print_exception(e)
            text = f"どうやら{role_name}の機嫌が悪いらしい...\n```\n{e}\n```"
            embed = discord.Embed(description=text, color=role_info["博麗霊夢"]['color'])
            await message.reply(text)

@client.event
async def on_message(message: discord.Message):
    if message.author.bot or message.type not in (discord.MessageType.default, discord.MessageType.reply):
        return

    if len(message.role_mentions) == 1:
        if message.role_mentions[0].name in role_info.keys():
            await handle_message(message, message.role_mentions[0].name)
    elif len(message.role_mentions) >= 2:
        count = 0
        role_names = []
        for role in message.role_mentions:
            if role.name in role_info.keys():
                count += 1
                role_names.append(role.name)
        if len(message.role_mentions) == count:
            await handle_message_fukusuu(message, "、".join(role_names))

    if message.reference is not None:
        if message.reference.resolved is not None:
            if message.reference.resolved.author.id == 1226065401650352148:
                if len(message.reference.resolved.embeds) >= 1:
                    print(message.reference.resolved.embeds[0].author.name)
                    if message.reference.resolved.embeds[0].author.name in list(role_info.keys()):
                        await handle_message(message, message.reference.resolved.embeds[0].author.name)

async def save():
    conn = await asyncpg.connect(os.getenv("dsn"))
    for key, value in chat_rooms.items():
        await conn.execute('INSERT INTO chat_rooms (id, data) VALUES ($1,$2)', key, value)
    await conn.close()

def sigterm_handler(a, b):
    asyncio.create_task(save())
    print("Received SIGTERM, exiting gracefully")
    sys.exit(0)

# SIGTERMシグナルハンドラを設定
signal.signal(signal.SIGTERM, sigterm_handler)

keep_alive()
client.run(os.getenv("discord"))