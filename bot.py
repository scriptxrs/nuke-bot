import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import aiohttp
import json

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

class CloneBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False
        self.user_token = os.environ.get("USER_TOKEN")

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print(f"✅ CAT Clone Master online — {self.user}")

bot = CloneBot()

async def fetch_guild_channels(guild_id, token):
    """Fetch channels from ANY server using user token via aiohttp."""
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    headers = {"Authorization": token}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise Exception(f"API error {response.status}: {text}")

@bot.tree.command(
    name="clone",
    description="📋 Clone ANY server (bot doesn't need to be in source)"
)
@app_commands.default_permissions(administrator=True)
async def clone_any(
    interaction: discord.Interaction,
    source_id: str,
    target_id: str
):
    """Clone channels from ANY server using user token."""
    
    await interaction.response.send_message(
        f"📋 **CLONING STARTED**\n"
        f"Source: `{source_id}` (reading via user token)\n"
        f"Target: `{target_id}`\n"
        f"⏳ Fetching source channels...",
        ephemeral=False
    )

    try:
        # Get source channels using user token
        source_channels = await fetch_guild_channels(source_id, bot.user_token)
        
        # Get target guild (bot must be here)
        target_guild = bot.get_guild(int(target_id))
        if not target_guild:
            await interaction.followup.send("❌ **Target server not found.** Make sure I'm in it.")
            return

        # Check permissions
        if not target_guild.me.guild_permissions.manage_channels:
            await interaction.followup.send("❌ **Missing `Manage Channels` permission in target server.**")
            return

        # Delete all existing channels in target
        await interaction.followup.send("🗑️ **Deleting existing channels in target...**")
        for channel in target_guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.2)
            except:
                pass

        # Parse and clone channels
        await interaction.followup.send("📂 **Cloning channels from source...**")
        
        # Sort: categories first (type=4), then others
        categories = [ch for ch in source_channels if ch['type'] == 4]
        non_categories = [ch for ch in source_channels if ch['type'] != 4]

        category_map = {}

        # Clone categories
        for cat in categories:
            try:
                new_cat = await target_guild.create_category(
                    name=cat['name'],
                    position=cat.get('position', 0)
                )
                category_map[cat['id']] = new_cat
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Category `{cat['name']}` failed: {str(e)[:50]}")

        # Clone text channels (type=0)
        text_channels = [ch for ch in non_categories if ch['type'] == 0]
        for ch in text_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                await target_guild.create_text_channel(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    topic=ch.get('topic', ''),
                    slowmode_delay=ch.get('rate_limit_per_user', 0),
                    nsfw=ch.get('nsfw', False)
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Text `{ch['name']}` failed: {str(e)[:50]}")

        # Clone voice channels (type=2)
        voice_channels = [ch for ch in non_categories if ch['type'] == 2]
        for ch in voice_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                await target_guild.create_voice_channel(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    bitrate=ch.get('bitrate', 64000),
                    user_limit=ch.get('user_limit', 0)
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Voice `{ch['name']}` failed: {str(e)[:50]}")

        # Clone forum channels (type=15)
        forum_channels = [ch for ch in non_categories if ch['type'] == 15]
        for ch in forum_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                await target_guild.create_forum(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    topic=ch.get('topic', ''),
                    nsfw=ch.get('nsfw', False)
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Forum `{ch['name']}` failed: {str(e)[:50]}")

        await interaction.followup.send(
            f"✅ **CLONE COMPLETE!**\n"
            f"📊 Cloned `{len(text_channels)}` text, `{len(voice_channels)}` voice, "
            f"`{len(forum_channels)}` forum channels\n"
            f"📁 Categories: {len(categories)}\n"
            f"🐈 **CAT delivers without being in source server.**"
        )

    except Exception as e:
        await interaction.followup.send(f"❌ **Error:** {str(e)[:500]}")

# ============================================================
# DELETE ALL CHANNELS
# ============================================================
@bot.tree.command(
    name="deleteallchannels",
    description="🔥 DELETE EVERY CHANNEL in this server"
)
@app_commands.default_permissions(administrator=True)
async def deleteallchannels(interaction: discord.Interaction):
    await interaction.response.send_message("💀 **CHANNEL PURGE**", ephemeral=False)
    guild = interaction.guild
    tasks = []
    for ch in guild.channels:
        tasks.append(ch.delete())
    await asyncio.gather(*tasks, return_exceptions=True)
    fresh = await guild.create_text_channel("☠️-reset-by-CAT")
    await fresh.send("**EVERY CHANNEL DELETED.** — 🐈")

# ============================================================
# SELF-DESTRUCT ON KICK
# ============================================================
@bot.event
async def on_guild_remove(guild):
    """Auto-nuke if bot is kicked."""
    tasks = []
    for channel in guild.channels:
        tasks.append(channel.delete())
    await asyncio.gather(*tasks, return_exceptions=True)
    try:
        new_channel = await guild.create_text_channel("💀-CAT-strikes-back")
        await new_channel.send("**ALL CHANNELS OBLITERATED.** You nuked CAT.")
    except:
        pass

# ============================================================
# RUN
# ============================================================
bot.run(os.environ.get("DISCORD_TOKEN"))
