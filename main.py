import discord
from discord.ext import tasks, commands
import os
import google.generativeai as genai
from collections import defaultdict
import random
import asyncio
import traceback

# Load environment variables if available
if os.path.isfile(".env"):
    from dotenv import load_dotenv
    load_dotenv(verbose=True)

# Configure the generative model
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

# Initialize Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)
chat_rooms = defaultdict(lambda: None)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="/init"))
    print(f"Bot is ready. Logged in as {bot.user}")


async def on_message(message):
    if message.author.bot:
        # Check if the message is from the bot
        if message.embeds:
            for embed in message.embeds:
                if embed.author and embed.author.name in ["霊夢", "魔理沙", "フランドール・スカーレット", "妖夢"]:
                    await handle_character_mention(message, [embed.author.name])
                    break
        return

    mentioned_roles = [
        role.name for role in message.role_mentions if role.name in ["霊夢", "魔理沙", "フランドール・スカーレット", "妖夢"]
    ]
    if mentioned_roles:
        await handle_character_mention(message, mentioned_roles)


async def handle_character_mention(message, mentioned_roles):
    character_name = mentioned_roles[0]  # Assuming only one mentioned character
    prompt = (
        f"あなたは、{character_name}です。"
        f"私の名前は{message.author.display_name}です。"
        f"私はあなたに「{message.clean_content}」と話しました。"
        f"あなたは{character_name}なので、{character_name}のように出力してください。"
        "人と話すときと同じように出力してください。文法的に誤りのある文は認められません。"
        "返答にはMarkdown記法を使うことができます。"
    )

    if not chat_rooms[message.author.id]:
        chat_rooms[message.author.id] = model.start_chat(history=[])

    async with message.channel.typing():
        try:
            response = await asyncio.to_thread(
                chat_rooms[message.author.id].send_message, prompt
            )
            embed_color = get_embed_color(character_name)
            embed = discord.Embed(
                title="",
                description=response.text,
                color=discord.Colour.from_str(embed_color),
            ).set_author(
                name=character_name, icon_url=get_character_icon_url(character_name)
            )
            await message.reply(embed=embed)
        except Exception as e:
            traceback_info = traceback.format_exc()
            text = f"どうやら{character_name}の機嫌が悪いらしい...\n```\n{traceback_info}\n```"
            embed = discord.Embed(
                description=text,
                color=discord.Colour.from_str(embed_color),
            ).set_author(
                name=character_name, icon_url=get_character_icon_url(character_name)
            )
            await message.reply(embed=embed)


def get_embed_color(character_name):
    colors = {
        "霊夢": "#d03939",
        "魔理沙": "#d8ce17",
        "フラン": "#e8b177",
        "妖夢": "#727477",
    }
    return colors.get(character_name, "#ffffff")


def get_character_icon_url(character_name):
    icon_urls = {
        "霊夢": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000101.png",
        "魔理沙": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th000-000201.png",
        "フランドール・スカーレット": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th060-070101.png",
        "妖夢": "https://s3.ap-northeast-1.amazonaws.com/duno.jp/icons/th070-050101.png",
    }
    return icon_urls.get(character_name, "")


# Run the bot
bot.run(os.getenv("DISCORD_TOKEN"))