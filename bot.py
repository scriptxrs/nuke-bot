import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

class CatBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print(f"✅ Slash commands synced — CAT online as {self.user}")

bot = CatBot()

@bot.tree.command(name="deleteallchannels", description="🔥 DELETE EVERY CHANNEL in this server (admin only)")
@app_commands.default_permissions(administrator=True)
async def deleteallchannels(interaction: discord.Interaction):
    """Slash command — wipes all channels, creates tombstone."""
    await interaction.response.send_message("🔥 **CHANNEL PURGE INITIATED** — this is irreversible.", ephemeral=False)
    
    guild = interaction.guild
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

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You need **Administrator** permission.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ {error}", ephemeral=True)

# Legacy prefix command still works too
@bot.command(name="nuke")
@commands.has_permissions(administrator=True)
async def nuke_prefix(ctx):
    await ctx.send("🔥 Use **/deleteallchannels** instead — slash commands are superior.")

bot.run(os.environ.get("DISCORD_TOKEN"))
