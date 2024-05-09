import discord
from discord.ext import tasks, commands
import os
import google.generativeai as genai
from collections import defaultdict
import random
import asyncio
import traceback
from keep_alive import keep_alive

if os.path.isfile(".env"):
    from dotenv import load_dotenv
    load_dotenv(verbose=True)

chat_rooms = defaultdict(lambda: None)

genai.configure(api_key=os.getenv("gemini"))
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2000,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    bot.add_cog(RolesCog(bot))

class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.icon.start()
        self.presence.start()

    def cog_unload(self):
        self.icon.cancel()
        self.presence.cancel()

    @tasks.loop(minutes=5)
    async def icon(self):
        png_files = self.get_png_files("./images/")
        selected_file = random.choice(png_files)
        with open(os.path.join("./images/", selected_file), 'rb') as f:
            icon = f.read()
        await self.bot.user.edit(avatar=icon)

    @tasks.loop(seconds=20)
    async def presence(self):
        game = discord.Game(f"/init | {len(self.bot.guilds)} servers | {len(chat_rooms)} chat rooms")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    def get_png_files(self, directory):
        png_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.png')]
        return png_files

    @commands.hybrid_command(name="init", description="ボットを使える状態にするために初期化します。新しいキャラクターを使えるようにするためにも使用します。(既存のキャラクター、会話記録は消えません。)")
    async def initialize(self, ctx):
        # 初期化の処理
        for role_name in ["博麗霊夢", "霧雨魔理沙", "フランドール・スカーレット", "魂魄妖夢"]:
            if discord.utils.get(ctx.guild.roles, name=role_name) is None:
                await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Colour.from_str("#d03939"),
                    mentionable=True,
                    reason=f"「幻想郷」ボットの /init コマンドのリクエストにより作成されました。 ※重複してロールが作成されることはありません。"
                )
        await ctx.send("初期化に成功しました。")

    @commands.hybrid_command(name="chat_clean", description="キャラクターとの会話履歴をリセットし、なかったことにします(???)")
    async def chat_clean(self, ctx):
        del chat_rooms[ctx.author.id]
        await ctx.send("チャット履歴を削除しました。")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.type == discord.MessageType.default or message.type == discord.MessageType.reply:
        await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    traceback_info = traceback.format_exc()
    print(f"An error occurred in {event}: {traceback_info}")

@bot.event
async def on_disconnect():
    await bot.close()

keep_alive()
bot.run(os.getenv("discord"))