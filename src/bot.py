
from env import API_KEY, GUILD_ID
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/",intents=intents)
guild = bot.get_guild(GUILD_ID)


@bot.tree.command(
    name="test",
    guild=guild,
)
async def test(ctx: commands.Context):
    await ctx.send("Test")


bot.run(API_KEY)
