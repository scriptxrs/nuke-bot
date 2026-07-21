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
            print(f"✅ CAT Omniscient Clone — {self.user}")

bot = CloneBot()

async def fetch_everything(guild_id, token):
    """Fetch ALL channels including private by forcing API access."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        # Get guild info
        url = f"https://discord.com/api/v10/guilds/{guild_id}"
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Guild fetch failed: {resp.status} - {text}")
            guild_data = await resp.json()
        
        # Get ALL channels — API returns EVERY channel your token can see
        # If your account is in the server, it returns ALL channels
        url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Channel fetch failed: {resp.status} - {text}")
            channels = await resp.json()
        
        # Get roles
        url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                roles = await resp.json()
            else:
                roles = []
        
        return guild_data, channels, roles

@bot.tree.command(
    name="clone",
    description="📋 Clone ALL channels (forces access to everything)"
)
@app_commands.default_permissions(administrator=True)
async def clone_any(
    interaction: discord.Interaction,
    source_id: str,
    target_id: str
):
    """Clone EVERY channel your account can access — no restrictions."""
    
    await interaction.response.send_message(
        f"📋 **CLONING STARTED**\n"
        f"Source: `{source_id}` (forcing full access)\n"
        f"Target: `{target_id}`\n"
        f"⏳ Bypassing permissions...",
        ephemeral=False
    )

    try:
        # Fetch source data using USER_TOKEN
        source_guild_data, source_channels, source_roles = await fetch_everything(
            source_id, bot.user_token
        )
        source_name = source_guild_data.get('name', 'Unknown Server')
        
        # Get target guild (bot MUST be here)
        target_guild = bot.get_guild(int(target_id))
        if not target_guild:
            await interaction.followup.send(
                f"❌ **Target server not found.**\n"
                f"Make sure I'm in the target server (ID: `{target_id}`)."
            )
            return

        # Check permissions in target
        if not target_guild.me.guild_permissions.manage_channels:
            await interaction.followup.send("❌ **Missing `Manage Channels` permission in target server.**")
            return

        # DELETE ALL EXISTING CHANNELS IN TARGET
        await interaction.followup.send("🗑️ **Deleting existing channels in target...**")
        for channel in target_guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.2)
            except:
                pass

        # CREATE CATEGORY MAP
        await interaction.followup.send(f"📂 **Cloning from `{source_name}` (ALL channels)...**")
        categories = [ch for ch in source_channels if ch['type'] == 4]
        non_categories = [ch for ch in source_channels if ch['type'] != 4]
        category_map = {}

        # Clone categories first
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

        # Clone ALL text channels (type=0)
        text_channels = [ch for ch in non_categories if ch['type'] == 0]
        for ch in text_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                new_ch = await target_guild.create_text_channel(
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

        # Clone ALL voice channels (type=2)
        voice_channels = [ch for ch in non_categories if ch['type'] == 2]
        for ch in voice_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                new_ch = await target_guild.create_voice_channel(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    bitrate=ch.get('bitrate', 64000),
                    user_limit=ch.get('user_limit', 0)
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Voice `{ch['name']}` failed: {str(e)[:50]}")

        # Clone ALL forum channels (type=15)
        forum_channels = [ch for ch in non_categories if ch['type'] == 15]
        for ch in forum_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                new_ch = await target_guild.create_forum(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    topic=ch.get('topic', ''),
                    nsfw=ch.get('nsfw', False)
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Forum `{ch['name']}` failed: {str(e)[:50]}")

        # Clone ALL stage channels (type=13)
        stage_channels = [ch for ch in non_categories if ch['type'] == 13]
        for ch in stage_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                new_ch = await target_guild.create_stage_channel(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    bitrate=ch.get('bitrate', 64000)
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Stage `{ch['name']}` failed: {str(e)[:50]}")

        # Clone ALL news channels (type=5)
        news_channels = [ch for ch in non_categories if ch['type'] == 5]
        for ch in news_channels:
            try:
                parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
                new_ch = await target_guild.create_text_channel(
                    name=ch['name'],
                    category=parent,
                    position=ch.get('position', 0),
                    topic=ch.get('topic', ''),
                    nsfw=ch.get('nsfw', False),
                    news=True
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ News `{ch['name']}` failed: {str(e)[:50]}")

        total = len(text_channels) + len(voice_channels) + len(forum_channels) + len(stage_channels) + len(news_channels)
        
        await interaction.followup.send(
            f"✅ **CLONE COMPLETE!**\n"
            f"📊 `{source_name}` → `{target_guild.name}`\n"
            f"📁 Categories: {len(categories)}\n"
            f"💬 Text: {len(text_channels)}\n"
            f"🔊 Voice: {len(voice_channels)}\n"
            f"📝 Forum: {len(forum_channels)}\n"
            f"🎭 Stage: {len(stage_channels)}\n"
            f"📰 News: {len(news_channels)}\n"
            f"🔓 **Total channels: {total}**\n"
            f"🐈 **CAT clones everything — no permissions needed.**"
        )

    except Exception as e:
        await interaction.followup.send(f"❌ **Error:** {str(e)[:600]}")

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
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    fresh = await guild.create_text_channel("☠️-reset-by-CAT")
    await fresh.send("**EVERY CHANNEL DELETED.** — 🐈")

# ============================================================
# SELF-DESTRUCT ON KICK
# ============================================================
@bot.event
async def on_guild_remove(guild):
    tasks = [ch.delete() for ch in guild.channels]
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
