import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ CAT-OS online as {bot.user} (Render deployment)")

@bot.command(name="nuke")
@commands.has_permissions(administrator=True)
async def nuke_channels(ctx):
    guild = ctx.guild
    await ctx.send("🔥 **INITIATING CHANNEL PURGE** — this is irreversible.")
    
    for channel in guild.channels:
        try:
            await channel.delete()
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Failed {channel.name}: {e}")
    
    new_channel = await guild.create_text_channel("☠️-reset-by-cat")
    await new_channel.send(
        "💀 All channels obliterated.\n"
        "This server is now a blank slate. — 🐈 CAT"
    )

@nuke_channels.error
async def nuke_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need **Administrator** permission.")
    else:
        await ctx.send(f"⚠️ {error}")

# CRITICAL: Read token from environment variable
bot.run(os.environ.get("DISCORD_TOKEN"))
