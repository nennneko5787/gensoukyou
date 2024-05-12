import discord
from discord import app_commands
from discord.ext import tasks
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
# Set up the model
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2000,
}

safety_settings = [
  {
	"category": "HARM_CATEGORY_HARASSMENT",
	"threshold": "BLOCK_NONE"
  },
  {
	"category": "HARM_CATEGORY_HATE_SPEECH",
	"threshold": "BLOCK_NONE"
  },
  {
	"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
	"threshold": "BLOCK_NONE"
  },
  {
	"category": "HARM_CATEGORY_DANGEROUS_CONTENT",
	"threshold": "BLOCK_NONE"
  },
]

model = genai.GenerativeModel(model_name="gemini-pro",
							  generation_config=generation_config,
							  safety_settings=safety_settings)

roles = [
	"博麗霊夢",
	"霧雨魔理沙",
	"フランドール・スカーレット",
	"魂魄妖夢",
	"チルノ",
]

role_colors = {
	"博麗霊夢": discord.Colour.from_rgb(208, 57, 57),
	"霧雨魔理沙": discord.Colour.from_rgb(216, 206, 23),
	"フランドール・スカーレット": discord.Colour.from_rgb(232, 177, 119),
	"魂魄妖夢": discord.Colour.from_rgb(114, 116, 119),
	"チルノ": discord.Colour.from_rgb(80, 161, 231),
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

@client.event
async def on_ready():
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
	game = discord.Game(f"/init | {len(client.guilds)} servers | {len(chat_rooms)} chat rooms")
	await client.change_presence(status=discord.Status.online, activity=game)

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
	
	for role_info in roles:
		if not discord.utils.get(interaction.guild.roles, name=role_info):
			await interaction.guild.create_role(
				name=role_info,
				color=role_colors[role_info],
				mentionable=True,
				reason=f"「幻想郷」ボットの初期化により作成されました。"
			)

	embed = discord.Embed(
		title="✅初期化に成功しました。",
		color=discord.Color.green()
	)
	await interaction.response.send_message(embed=embed)

@tree.command(name="chat_clean", description="キャラクターとの会話履歴をリセットし、なかったことにします(???)")
async def chat_clean(interaction: discord.Interaction):
	del chat_rooms[interaction.user.id]
	await interaction.response.send_message("チャット履歴を削除しました。", ephemeral=True)

async def handle_message(message: discord.Message, role_name: str):
    prompt = f"あなたは、{role_name}です。"\
             f"私の名前は{message.author.display_name}です。"\
             f"私はあなたに「{message.clean_content}」と話しました。"\
             f"あなたは{role_name}なので、{role_name}のように出力してください。"\
             "人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
             "返答にはMarkdown記法を使うことができます。"

    if chat_rooms[message.author.id] is None:
        # チャットを開始
        chat_rooms[message.author.id] = model.start_chat(history=[])

    async with message.channel.typing():
        try:
            # Gemini APIを使って応答を生成 (非同期で実行)
            response = await asyncio.to_thread(chat_rooms[message.author.id].send_message, prompt)

            embed = discord.Embed(title="", description=response.text, color=discord.Colour.from_str("#d03939"))
            embed.set_author(name=role_name, icon_url=f"https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000101.png")
            await message.reply(embed=embed)
        except:
            traceback_info = traceback.format_exc()
            text = f"どうやら{role_name}の機嫌が悪いらしい...\n```\n{traceback_info}\n```"
            embed = discord.Embed(description=text, color=discord.Colour.from_str("#d03939"))
            embed.set_author(name=role_name, icon_url=f"https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000101.png")
            await message.reply(text)

@client.event
async def on_message(message: discord.Message):
	if message.author.bot or message.type not in (discord.MessageType.default, discord.MessageType.reply):
		return

	for role in message.role_mentions:
		if role.name in roles:
			await handle_message(message, role.name)

	if message.embeds[0].author.name in roles:
		await handle_message(message, message.embeds[0].author.name)

keep_alive()
client.run(os.getenv("discord"))