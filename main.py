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
	if interaction.user.guild_permissions.administrator is not True:
		embed = discord.Embed(
			title="あなたにはこのコマンドを実行する権限はありません！",
			description="**このコマンドを実行するには以下の権限が必要です。**\n**管理者** *(ADMINISTRATOR)*",
			color=discord.Color.red()
		)
		await interaction.response.send_message(embed=embed, ephemeral=True)
		return
	
	if interaction.guild.me.guild_permissions.manage_roles is not True:
		embed = discord.Embed(
			title="ボットに必要な権限が足りません！",
			description="**以下の権限を付与してください。**\n**ロールの管理** *(MANAGE_ROLES)*",
			color=discord.Color.red()
		)
		await interaction.response.send_message(embed=embed, ephemeral=True)
		return
	
	if discord.utils.get(interaction.guild.roles, name='博麗霊夢') is None:
		await interaction.guild.create_role(
			name="博麗霊夢",
			color=discord.Colour.from_str("#d03939"),
			mentionable=True,
			reason="「幻想郷」ボットの /init コマンドのリクエストにより作成されました。 ※重複してロールが作成されることはありません。"
		)
	if discord.utils.get(interaction.guild.roles, name='霧雨魔理沙') is None:
		await interaction.guild.create_role(
			name="霧雨魔理沙",
			color=discord.Colour.from_str("#d8ce17"),
			mentionable=True,
			reason="「幻想郷」ボットの /init コマンドのリクエストにより作成されました。 ※重複してロールが作成されることはありません。"
		)
	if discord.utils.get(interaction.guild.roles, name='フランドール・スカーレット') is None:
		await interaction.guild.create_role(
			name="フランドール・スカーレット",
			color=discord.Colour.from_str("#e8b177"),
			mentionable=True,
			reason="「幻想郷」ボットの /init コマンドのリクエストにより作成されました。 ※重複してロールが作成されることはありません。"
		)
	if discord.utils.get(interaction.guild.roles, name='魂魄妖夢') is None:
		await interaction.guild.create_role(
			name="魂魄妖夢",
			color=discord.Colour.from_str("#727477"),
			mentionable=True,
			reason="「幻想郷」ボットの /init コマンドのリクエストにより作成されました。 ※重複してロールが作成されることはありません。"
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

@client.event
async def on_message(message: discord.Message):
	if message.type == discord.MessageType.default or message.type == discord.MessageType.reply:
		if message.author.bot == False:
			mentioned = False
			if discord.utils.find(lambda r: r.name == '博麗霊夢', message.role_mentions) or discord.utils.find(lambda e: e.author.name == '霧雨魔理沙', message.embeds):
				await asyncio.create_task(博麗霊夢(message))
				mentioned = True
			if discord.utils.find(lambda r: r.name == '霧雨魔理沙', message.role_mentions) or discord.utils.find(lambda e: e.author.name == '霧雨魔理沙', message.embeds):
				await asyncio.create_task(霧雨魔理沙(message))
				mentioned = True
			if discord.utils.find(lambda r: r.name == 'フランドール・スカーレット', message.role_mentions) or discord.utils.find(lambda e: e.author.name == 'フランドール・スカーレット', message.embeds):
				await asyncio.create_task(フランドール＿スカーレット(message))
				mentioned = True
			if discord.utils.find(lambda r: r.name == '魂魄妖夢', message.role_mentions) or discord.utils.find(lambda e: e.author.name == '魂魄妖夢', message.embeds):
				await asyncio.create_task(魂魄妖夢(message))
				mentioned = True

			if discord.utils.find(lambda r: r.id == 1226065401650352148, message.mentions) and mentioned == False:
				embed = discord.Embed(
					title="このボットの使い方",
					description=f"{discord.utils.find(lambda r: r.name == '博麗霊夢', message.guild.roles).mention} や {discord.utils.find(lambda r: r.name == '霧雨魔理沙', message.guild.roles).mention} にメンションするだけ。"
				)
				await asyncio.create_task(message.channel.send(embed=embed))

async def 博麗霊夢(message: discord.Message):
	prompt = "あなたは、博麗霊夢です。"\
			f"私の名前は{message.author.display_name}です。私はあなたに「{message.clean_content}」と話しました。あなたは博麗霊夢なので、博麗霊夢のように出力してください。人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
			"返答にはMarkdown記法を使うことができます。"
#	if message.type == discord.MessageType.reply:
#		prompt = f"{prompt}また、私は、{message.reference.cached_message.author.display_name}さんの「{message.reference.cached_message.clean_content}」というメッセージに返信しています。"

	if chat_rooms[message.author.id] == None:
		# チャットを開始
		chat_rooms[message.author.id] = model.start_chat(history=[])

	async with message.channel.typing():
		try:
			# Gemini APIを使って応答を生成 (非同期で実行)
			response = await asyncio.to_thread(chat_rooms[message.author.id].send_message, prompt)

			embed = discord.Embed(title="",description=response.text,color=discord.Colour.from_str("#d03939")).set_author(name="博麗霊夢", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000101.png")
			await message.reply(embed=embed)
		except:
			traceback_info = traceback.format_exc()
			text = f"どうやら博麗霊夢の機嫌が悪いらしい...\n```\n{traceback_info}\n```"
			embed = discord.Embed(description=text,color=discord.Colour.from_str("#d03939")).set_author(name="博麗霊夢", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000101.png")
			await message.reply(text)
	return

async def 霧雨魔理沙(message: discord.Message):
	prompt = "あなたは、霧雨魔理沙です。"\
			f"私の名前は{message.author.display_name}です。私はあなたに「{message.clean_content}」と話しました。あなたは霧雨魔理沙なので、霧雨魔理沙のように出力してください。人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
			"返答にはMarkdown記法を使うことができます。"
#	if message.type == discord.MessageType.reply:
#		prompt = f"{prompt}また、私は、{message.reference.cached_message.author.display_name}さんの「{message.reference.cached_message.clean_content}」というメッセージに返信しています。"

	if chat_rooms[message.author.id] == None:
		# チャットを開始
		chat_rooms[message.author.id] = model.start_chat(history=[])

	async with message.channel.typing():
		try:
			# Gemini APIを使って応答を生成 (非同期で実行)
			response = await asyncio.to_thread(chat_rooms[message.author.id].send_message, prompt)

			embed = discord.Embed(title="",description=response.text,color=discord.Colour.from_str("#d8ce17")).set_author(name="霧雨魔理沙", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000201.png")
			await message.reply(embed=embed)
		except:
			traceback_info = traceback.format_exc()
			text = f"どうやら霧雨魔理沙の機嫌が悪いらしい...\n```\n{traceback_info}\n```"
			embed = discord.Embed(description=text,color=discord.Colour.from_str("#d8ce17")).set_author(name="霧雨魔理沙", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000201.png")
			await message.reply(text)
	return

async def フランドール＿スカーレット(message: discord.Message):
	prompt = "あなたは、フランドール・スカーレットです。"\
			f"私の名前は{message.author.display_name}です。私はあなたに「{message.clean_content}」と話しました。あなたはフランドール・スカーレットなので、フランドール・スカーレットのように出力してください。人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
			"返答にはMarkdown記法を使うことができます。"
#	if message.type == discord.MessageType.reply:
#		prompt = f"{prompt}また、私は、{message.reference.cached_message.author.display_name}さんの「{message.reference.cached_message.clean_content}」というメッセージに返信しています。"

	if chat_rooms[message.author.id] == None:
		# チャットを開始
		chat_rooms[message.author.id] = model.start_chat(history=[])

	async with message.channel.typing():
		try:
			# Gemini APIを使って応答を生成 (非同期で実行)
			response = await asyncio.to_thread(chat_rooms[message.author.id].send_message, prompt)

			embed = discord.Embed(title="",description=response.text,color=discord.Colour.from_str("#e8b177")).set_author(name="フランドール・スカーレット", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th060-070101.png")
			await message.reply(embed=embed)
		except:
			traceback_info = traceback.format_exc()
			text = f"どうやらフランドール・スカーレットの機嫌が悪いらしい...\n```\n{traceback_info}\n```"
			embed = discord.Embed(description=text,color=discord.Colour.from_str("#e8b177")).set_author(name="フランドール・スカーレット", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th060-070101.png")
			await message.reply(text)
	return

async def 魂魄妖夢(message: discord.Message):
	prompt = "あなたは、魂魄妖夢です。"\
			f"私の名前は{message.author.display_name}です。私はあなたに「{message.clean_content}」と話しました。あなたは魂魄妖夢なので、魂魄妖夢のように出力してください。人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"\
			"返答にはMarkdown記法を使うことができます。"
#	if message.type == discord.MessageType.reply:
#		prompt = f"{prompt}また、私は、{message.reference.cached_message.author.display_name}さんの「{message.reference.cached_message.clean_content}」というメッセージに返信しています。"

	if chat_rooms[message.author.id] == None:
		# チャットを開始
		chat_rooms[message.author.id] = model.start_chat(history=[])

	async with message.channel.typing():
		try:
			# Gemini APIを使って応答を生成 (非同期で実行)
			response = await asyncio.to_thread(chat_rooms[message.author.id].send_message, prompt)

			embed = discord.Embed(title="",description=response.text,color=discord.Colour.from_str("#727477")).set_author(name="魂魄妖夢", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th070-050101.png")
			await message.reply(embed=embed)
		except:
			traceback_info = traceback.format_exc()
			text = f"どうやら魂魄妖夢の機嫌が悪いらしい...\n```\n{traceback_info}\n```"
			embed = discord.Embed(description=text,color=discord.Colour.from_str("#727477")).set_author(name="魂魄妖夢", icon_url="https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th070-050101.png")
			await message.reply(text)
	return

keep_alive()
client.run(os.getenv("discord"))
