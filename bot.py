import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
import asyncio
import os
import aiohttp
from datetime import datetime, timedelta
import io
import threading
from flask import Flask, jsonify, render_template_string

# ============================================================
# FLASK WEB SERVER
# ============================================================
flask_app = Flask(__name__)

COMMANDS_DATA = [
    {"category": "🛡️ Moderation", "icon": "🛡️", "commands": [
        {"name": "/ban", "description": "Ban a user with confirm/cancel buttons", "permissions": "Ban Members"},
        {"name": "/kick", "description": "Kick a user with confirm/cancel buttons", "permissions": "Kick Members"},
        {"name": "/timeout", "description": "Timeout a user with custom duration", "permissions": "Moderate Members"},
        {"name": "/untimeout", "description": "Remove timeout from a user", "permissions": "Moderate Members"},
        {"name": "/mute", "description": "Mute a user (adds Muted role)", "permissions": "Manage Roles"},
        {"name": "/unmute", "description": "Unmute a user", "permissions": "Manage Roles"},
        {"name": "/punish", "description": "Open punishment selector menu", "permissions": "Moderate Members"},
        {"name": "/removeroles", "description": "Remove all roles from a user", "permissions": "Manage Roles"},
        {"name": "/nick", "description": "Change a user's nickname", "permissions": "Manage Nicknames"},
        {"name": "/slowmode", "description": "Set slowmode in a channel", "permissions": "Manage Channels"}
    ]},
    {"category": "🧹 Cleanup", "icon": "🧹", "commands": [
        {"name": "/clean", "description": "Deep clean chat (keeps files/images)", "permissions": "Manage Messages"},
        {"name": "/purge", "description": "Delete specific number of messages", "permissions": "Manage Messages"},
        {"name": "/clear", "description": "DELETE ALL messages in a channel", "permissions": "Manage Messages"},
        {"name": "/deletetext", "description": "Delete ONLY text messages (keep files)", "permissions": "Manage Messages"},
        {"name": "/deletefiles", "description": "Delete ONLY messages with files (keep text)", "permissions": "Manage Messages"}
    ]},
    {"category": "📤 Forward & Clone", "icon": "📤", "commands": [
        {"name": "/forward", "description": "Forward ONLY videos, photos, .txt (NO XML)", "permissions": "Administrator"},
        {"name": "/clone", "description": "Clone server structure", "permissions": "Administrator"}
    ]},
    {"category": "🔒 Server Control", "icon": "🔒", "commands": [
        {"name": "/lockdown", "description": "Lock down the entire server", "permissions": "Administrator"},
        {"name": "/unlock", "description": "Unlock the server", "permissions": "Administrator"},
        {"name": "/lockall", "description": "Lock ALL channels in this server", "permissions": "Administrator"},
        {"name": "/unlockall", "description": "Unlock ALL channels in this server", "permissions": "Administrator"},
        {"name": "/deleteallchannels", "description": "DELETE EVERY CHANNEL (with confirmation)", "permissions": "Administrator"}
    ]},
    {"category": "🎫 Tickets", "icon": "🎫", "commands": [
        {"name": "/ticket", "description": "Create a support ticket", "permissions": "Manage Channels"},
        {"name": "/closeticket", "description": "Close a ticket channel", "permissions": "Manage Channels"}
    ]},
    {"category": "📢 Utility", "icon": "📢", "commands": [
        {"name": "/help", "description": "Show all available commands", "permissions": "Everyone"},
        {"name": "/announce", "description": "Send an announcement embed", "permissions": "Administrator"},
        {"name": "/poll", "description": "Create a poll with reactions", "permissions": "Administrator"},
        {"name": "/setup", "description": "Setup CAT Security logs channel", "permissions": "Administrator"},
        {"name": "/stats", "description": "Show server statistics", "permissions": "Administrator"}
    ]},
    {"category": "🖱️ Context Menus", "icon": "🖱️", "commands": [
        {"name": "Right-click → Ban User", "description": "Quick ban from user menu", "permissions": "Ban Members"},
        {"name": "Right-click → Kick User", "description": "Quick kick from user menu", "permissions": "Kick Members"},
        {"name": "Right-click → Timeout User", "description": "Quick 60min timeout from user menu", "permissions": "Moderate Members"}
    ]}
]

PROTECTION_DATA = [
    {"icon": "🚨", "name": "Raid Detection", "description": "Auto-bans users when 5+ join in 1 minute"},
    {"icon": "🚨", "name": "Spam Detection", "description": "Auto-bans users sending 10+ messages in 5 seconds"},
    {"icon": "🚨", "name": "Mass Mention Detection", "description": "Auto-bans users mentioning 5+ users in one message"},
    {"icon": "🚨", "name": "New Account Detection", "description": "Auto-bans accounts under 24 hours old"},
    {"icon": "☢️", "name": "Nuke Detection", "description": "Auto-bans users deleting 3+ channels in 10 seconds"},
    {"icon": "💀", "name": "Self-Destruct", "description": "Deletes ALL channels if bot is kicked/banned"},
    {"icon": "📋", "name": "Full Logging", "description": "All actions logged to #cat-logs channel"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐱 CAT Bot - Command List</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 4rem;
            background: linear-gradient(135deg, #f7971e, #ffd200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { font-size: 1.2rem; color: #888; margin-top: 10px; }
        .header .status {
            display: inline-block;
            background: rgba(0,255,0,0.15);
            color: #0f0;
            padding: 8px 20px;
            border-radius: 20px;
            margin-top: 15px;
            font-size: 0.9rem;
            border: 1px solid rgba(0,255,0,0.2);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .stat-card .number {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #f7971e, #ffd200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-card .label { color: #888; margin-top: 5px; font-size: 0.9rem; }
        .category {
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .category-title {
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #ffd700;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .category-title span {
            background: rgba(255,215,0,0.1);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            color: #aaa;
        }
        .command-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 12px;
        }
        .command-item {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 14px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
            border-left: 3px solid #ffd700;
        }
        .command-item:hover {
            background: rgba(255,255,255,0.08);
            transform: translateX(5px);
        }
        .command-left { display: flex; flex-direction: column; }
        .command-name { font-weight: 600; color: #ffd700; font-size: 1rem; }
        .command-desc { font-size: 0.85rem; color: #aaa; margin-top: 2px; }
        .command-perm {
            font-size: 0.7rem;
            background: rgba(255,0,0,0.15);
            color: #ff6b6b;
            padding: 3px 10px;
            border-radius: 12px;
            white-space: nowrap;
            border: 1px solid rgba(255,0,0,0.1);
        }
        .auto-section {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid rgba(255,255,255,0.05);
        }
        .auto-section h2 { font-size: 2rem; color: #ff6b6b; margin-bottom: 20px; }
        .auto-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }
        .auto-item {
            background: rgba(255,0,0,0.05);
            border-radius: 10px;
            padding: 15px 20px;
            border-left: 3px solid #ff6b6b;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .auto-item .icon { font-size: 1.8rem; }
        .auto-item .info h4 { font-size: 1rem; color: #fff; }
        .auto-item .info p { font-size: 0.85rem; color: #888; }
        .footer {
            text-align: center;
            padding: 40px 0 20px;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 40px;
            color: #555;
            font-size: 0.9rem;
        }
        @media (max-width: 600px) {
            .header h1 { font-size: 2.5rem; }
            .command-grid { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .command-item { flex-direction: column; align-items: flex-start; gap: 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐱 CAT Bot</h1>
            <p>Ultimate Discord Security & Utility Bot</p>
            <div class="status">🟢 Online • {{ time }}</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{{ total_commands }}</div><div class="label">Total Commands</div></div>
            <div class="stat-card"><div class="number">{{ total_categories }}</div><div class="label">Categories</div></div>
            <div class="stat-card"><div class="number">{{ protection_count }}</div><div class="label">Protection Features</div></div>
            <div class="stat-card"><div class="number">🟢</div><div class="label">Status: Online</div></div>
        </div>
        {% for cat in commands %}
        <div class="category">
            <div class="category-title">{{ cat.icon }} {{ cat.category }} <span>{{ cat.commands|length }} commands</span></div>
            <div class="command-grid">
                {% for cmd in cat.commands %}
                <div class="command-item">
                    <div class="command-left">
                        <div class="command-name">{{ cmd.name }}</div>
                        <div class="command-desc">{{ cmd.description }}</div>
                    </div>
                    <div class="command-perm">{{ cmd.permissions }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
        <div class="auto-section">
            <h2>🛡️ Auto-Protection Features</h2>
            <div class="auto-grid">
                {% for feature in protection %}
                <div class="auto-item">
                    <div class="icon">{{ feature.icon }}</div>
                    <div class="info">
                        <h4>{{ feature.name }}</h4>
                        <p>{{ feature.description }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        <div class="footer">
            🐱 CAT Bot • Built with ❤️ • All commands are slash (/) commands
            <br><small>Total: {{ total_commands }} commands • {{ protection_count }} protection features</small>
        </div>
    </div>
</body>
</html>
"""

@flask_app.route('/')
def index():
    total_commands = sum(len(cat['commands']) for cat in COMMANDS_DATA)
    return render_template_string(
        HTML_TEMPLATE,
        commands=COMMANDS_DATA,
        protection=PROTECTION_DATA,
        total_commands=total_commands,
        total_categories=len(COMMANDS_DATA),
        protection_count=len(PROTECTION_DATA),
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@flask_app.route('/health')
def health():
    return {"status": "online", "timestamp": datetime.now().isoformat()}

def run_web_server():
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ============================================================
# DISCORD BOT
# ============================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="", intents=intents)
bot.user_token = os.environ.get("USER_TOKEN")

CONFIG = {
    "max_joins_per_minute": 5,
    "max_messages_per_second": 10,
    "max_mentions_per_message": 5,
    "max_new_account_age_hours": 24,
    "default_punishment": "ban",
    "log_channel_name": "cat-logs",
    "auto_setup": True,
    "target_channel_id": 1529285254148259960
}

# ============================================================
# LOGS CHANNEL SETUP
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
        log_channel = await guild.create_text_channel(CONFIG["log_channel_name"], category=category, overwrites=overwrites)
        await log_channel.send("🔒 **CAT SECURITY INITIALIZED**")
    return log_channel

async def log_action(guild, action, user, details=""):
    log_channel = discord.utils.get(guild.channels, name=CONFIG["log_channel_name"])
    if not log_channel:
        log_channel = await setup_logs_channel(guild)
    embed = discord.Embed(title=f"🔒 {action}", description=f"**User:** {user.mention} (`{user.id}`)\n{details}", color=discord.Color.red(), timestamp=datetime.utcnow())
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
            await user.timeout(timedelta(minutes=60), reason=f"CAT Security: {reason}")
            await log_action(guild, "⏰ TIMEOUT", user, f"60 minutes. Reason: {reason}")
            return "timed out"
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
# UI COMPONENTS
# ============================================================
class ConfirmView(View):
    def __init__(self, user, guild, action, reason, timeout=60):
        super().__init__(timeout=timeout)
        self.user = user
        self.guild = guild
        self.action = action
        self.reason = reason
        self.confirmed = False

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.confirmed = True
        self.stop()
        result = await punish_user(self.user, self.guild, self.reason, self.action)
        await interaction.followup.send(f"✅ **{self.user}** has been {result}.", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Action cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

class PunishmentSelect(View):
    def __init__(self, user, guild, reason, timeout=60):
        super().__init__(timeout=timeout)
        self.user = user
        self.guild = guild
        self.reason = reason
        self.selected = None

    @discord.ui.select(placeholder="Choose punishment...", options=[
        discord.SelectOption(label="🔨 Ban", value="ban", description="Permanently remove user"),
        discord.SelectOption(label="👢 Kick", value="kick", description="Remove user temporarily"),
        discord.SelectOption(label="⏰ Timeout", value="timeout", description="Mute for 60 minutes"),
        discord.SelectOption(label="🔇 Mute", value="mute", description="Add Muted role"),
        discord.SelectOption(label="⚔️ Remove Roles", value="remove_roles", description="Strip all roles"),
    ])
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        await interaction.response.defer()
        self.selected = select.values[0]
        self.stop()
        result = await punish_user(self.user, self.guild, self.reason, self.selected)
        await interaction.followup.send(f"✅ **{self.user}** has been {result}.", ephemeral=True)

class DeleteAllConfirmView(View):
    def __init__(self, guild, user, timeout=60):
        super().__init__(timeout=timeout)
        self.guild = guild
        self.user = user
        self.confirmed = False

    @discord.ui.button(label="💀 YES, DELETE ALL CHANNELS", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        self.confirmed = True
        self.stop()
        total = len(self.guild.channels)
        deleted = 0
        failed = 0
        for channel in self.guild.channels:
            try:
                await channel.delete()
                deleted += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                failed += 1
                await log_action(self.guild, "❌ DELETE FAILED", self.user, f"Channel: {channel.name}\nError: {str(e)[:100]}")
        try:
            new_channel = await self.guild.create_text_channel("☠️-reset-by-CAT")
            await new_channel.send(f"💀 **ALL CHANNELS DELETED!**\n🗑️ Deleted: {deleted} channels\n❌ Failed: {failed} channels\n🐈 CAT delivers.")
        except:
            pass
        await log_action(self.guild, "💀 ALL CHANNELS DELETED", self.user, f"Deleted {deleted} channels, failed {failed}")
        await interaction.followup.send(f"✅ **Deleted {deleted} channels**\n❌ Failed: {failed}\n💀 Server has been wiped.", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

class ClearConfirmView(View):
    def __init__(self, channel, guild, user, timeout=60):
        super().__init__(timeout=timeout)
        self.channel = channel
        self.guild = guild
        self.user = user
        self.confirmed = False

    @discord.ui.button(label="💀 YES, DELETE ALL", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        self.confirmed = True
        self.stop()
        deleted = 0
        try:
            while True:
                async for msg in self.channel.history(limit=100):
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.2)
                if not await self.channel.history(limit=1).flatten():
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            return
        await log_action(self.guild, "🧹 CHANNEL CLEARED", self.user, f"Cleared {deleted} messages in #{self.channel.name}")
        await interaction.followup.send(f"✅ **Deleted {deleted} messages** from #{self.channel.name}", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

class DeleteTextConfirmView(View):
    def __init__(self, channel, guild, user, limit, timeout=60):
        super().__init__(timeout=timeout)
        self.channel = channel
        self.guild = guild
        self.user = user
        self.limit = limit
        self.confirmed = False

    @discord.ui.button(label="🗑️ DELETE TEXT ONLY", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        self.confirmed = True
        self.stop()
        deleted = 0
        kept = 0
        async for msg in self.channel.history(limit=self.limit):
            if len(msg.attachments) == 0:
                await msg.delete()
                deleted += 1
                await asyncio.sleep(0.2)
            else:
                kept += 1
        await log_action(self.guild, "🗑️ TEXT DELETED", self.user, f"Deleted {deleted}, kept {kept} files")
        await interaction.followup.send(f"✅ Deleted {deleted} text, kept {kept} files", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

class DeleteFilesConfirmView(View):
    def __init__(self, channel, guild, user, limit, timeout=60):
        super().__init__(timeout=timeout)
        self.channel = channel
        self.guild = guild
        self.user = user
        self.limit = limit
        self.confirmed = False

    @discord.ui.button(label="🗑️ DELETE FILES ONLY", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        self.confirmed = True
        self.stop()
        deleted = 0
        kept = 0
        async for msg in self.channel.history(limit=self.limit):
            if len(msg.attachments) > 0:
                await msg.delete()
                deleted += 1
                await asyncio.sleep(0.2)
            else:
                kept += 1
        await log_action(self.guild, "🗑️ FILES DELETED", self.user, f"Deleted {deleted} files, kept {kept} text")
        await interaction.followup.send(f"✅ Deleted {deleted} files, kept {kept} text", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
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
    print(f"✅ CAT Bot online — {bot.user}")
    if CONFIG["auto_setup"]:
        for guild in bot.guilds:
            await setup_logs_channel(guild)
    await bot.tree.sync()
    print("✅ Slash commands synced")

@bot.event
async def on_member_join(member):
    guild = member.guild
    now = datetime.utcnow()
    if guild.id not in join_timestamps:
        join_timestamps[guild.id] = []
    join_timestamps[guild.id].append(now)
    join_timestamps[guild.id] = [t for t in join_timestamps[guild.id] if t > now - timedelta(minutes=1)]
    if len(join_timestamps[guild.id]) > CONFIG["max_joins_per_minute"]:
        await log_action(guild, "🚨 RAID DETECTED", member, f"Mass joins: {len(join_timestamps[guild.id])} in 1 minute")
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
    message_cache[key] = [(t, c) for t, c in message_cache[key] if t > now - timedelta(seconds=5)]
    if len(message_cache[key]) > CONFIG["max_messages_per_second"] * 5:
        await log_action(guild, "🚨 SPAM DETECTED", message.author, f"{len(message_cache[key])} messages in 5 seconds")
        await punish_user(message.author, guild, "Message spam")
        await message.delete()
        return
    if len(message.mentions) > CONFIG["max_mentions_per_message"]:
        await log_action(guild, "🚨 MASS MENTION", message.author, f"Mentioned {len(message.mentions)} users")
        await punish_user(message.author, guild, "Mass mentions")
        await message.delete()
        return
    if (datetime.utcnow() - message.author.created_at).total_seconds() < CONFIG["max_new_account_age_hours"] * 3600:
        await log_action(guild, "🚨 NEW ACCOUNT", message.author, f"Account age: {(datetime.utcnow() - message.author.created_at).total_seconds()/3600:.1f}h")
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
    deletion_cache[guild.id] = [t for t in deletion_cache[guild.id] if t > now - timedelta(seconds=10)]
    if len(deletion_cache[guild.id]) > 3:
        await log_action(guild, "☢️ NUKE DETECTED", guild.owner, f"{len(deletion_cache[guild.id])} channels deleted")
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                await punish_user(entry.user, guild, "Channel nuke")
                break

@bot.event
async def on_guild_remove(guild):
    for ch in guild.channels:
        try:
            await ch.delete()
        except:
            pass
    try:
        new = await guild.create_text_channel("💀-CAT-strikes-back")
        await new.send("**ALL CHANNELS OBLITERATED.** You nuked CAT.")
    except:
        pass

# ============================================================
# FILE DOWNLOAD HELPER
# ============================================================
async def download_file(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            return None

# ============================================================
# FORWARD — ONLY VIDEOS, PHOTOS, TXT (NO XML)
# ============================================================
async def forward_files_only(source_channel_id, target_channel, token, limit=2000):
    ALLOWED_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.tiff', '.svg',
        '.mp4', '.mov', '.avi', '.webm', '.mkv', '.flv', '.wmv', '.m4v', '.3gp', '.mpg', '.mpeg',
        '.txt'
    }
    
    BLOCKED_EXTENSIONS = {
        '.xml', '.json', '.yaml', '.yml', '.toml', '.csv', '.xlsx', '.xls',
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.zip', '.rar', '.7z',
        '.exe', '.msi', '.dmg', '.apk', '.deb', '.rpm'
    }
    
    messages = []
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": token}
        url = f"https://discord.com/api/v10/channels/{source_channel_id}/messages?limit=100"
        while len(messages) < limit:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    break
                data = await resp.json()
                if not data:
                    break
                messages.extend(data)
                last_id = data[-1]['id']
                url = f"https://discord.com/api/v10/channels/{source_channel_id}/messages?limit=100&before={last_id}"
                await asyncio.sleep(0.2)
    
    file_count = 0
    skipped_count = 0
    
    for msg in reversed(messages):
        try:
            author_name = msg['author']['username']
            author_id = msg['author']['id']
            timestamp = msg.get('timestamp', '')
            
            attachments = msg.get('attachments', [])
            if not attachments:
                continue
            
            has_allowed_file = False
            allowed_files = []
            
            for att in attachments:
                filename = att['filename'].lower()
                is_allowed = any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)
                is_blocked = any(filename.endswith(ext) for ext in BLOCKED_EXTENSIONS)
                
                if is_allowed and not is_blocked:
                    has_allowed_file = True
                    allowed_files.append(att)
                else:
                    skipped_count += 1
            
            if not has_allowed_file:
                continue
            
            header = f"📎 **{author_name}** (`{author_id}`) [{timestamp[:10]} {timestamp[11:19]}]:"
            await target_channel.send(header)
            await asyncio.sleep(0.3)
            
            for att in allowed_files:
                try:
                    file_url = att['url']
                    filename = att['filename']
                    file_size = att.get('size', 0)
                    
                    if file_size > 25 * 1024 * 1024:
                        await target_channel.send(f"⚠️ File too large: {filename} ({file_size/1024/1024:.1f}MB) - Skipped")
                        continue
                    
                    file_data = await download_file(file_url)
                    if file_data:
                        file_obj = discord.File(io.BytesIO(file_data), filename=filename)
                        await target_channel.send(file=file_obj)
                        file_count += 1
                        await asyncio.sleep(0.5)
                except Exception as e:
                    await target_channel.send(f"⚠️ Failed to download: {str(e)[:50]}")
            
            embeds = msg.get('embeds', [])
            for embed_data in embeds:
                embed_image = embed_data.get('image', {})
                embed_video = embed_data.get('video', {})
                
                if embed_image:
                    img_url = embed_image.get('url')
                    if img_url:
                        img_data = await download_file(img_url)
                        if img_data:
                            filename = f"embed_image_{datetime.utcnow().timestamp()}.png"
                            file_obj = discord.File(io.BytesIO(img_data), filename=filename)
                            await target_channel.send(f"🖼️ **Embed image from {author_name}:**", file=file_obj)
                            file_count += 1
                            await asyncio.sleep(0.5)
                
                if embed_video:
                    video_url = embed_video.get('url')
                    if video_url:
                        video_data = await download_file(video_url)
                        if video_data:
                            filename = f"embed_video_{datetime.utcnow().timestamp()}.mp4"
                            file_obj = discord.File(io.BytesIO(video_data), filename=filename)
                            await target_channel.send(f"🎬 **Embed video from {author_name}:**", file=file_obj)
                            file_count += 1
                            await asyncio.sleep(0.5)
        
        except Exception as e:
            continue
    
    return file_count, skipped_count

# ============================================================
# FETCH GUILD DATA
# ============================================================
async def fetch_guild_data(guild_id, token):
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": token}
        async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}", headers=headers) as resp:
            guild = await resp.json()
        async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers) as resp:
            channels = await resp.json()
        return guild, channels

# ============================================================
# SLASH COMMANDS
# ============================================================

# --- HELP COMMAND ---
@bot.tree.command(name="help", description="📋 Show all available commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐱 CAT Bot - Command List",
        description="Here are all available commands. Use `/` to see them in Discord.",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    for category in COMMANDS_DATA:
        cmd_list = "\n".join([f"`{cmd['name']}` — {cmd['description']} *(Perm: {cmd['permissions']})*" for cmd in category['commands']])
        embed.add_field(name=f"{category['icon']} {category['category']}", value=cmd_list, inline=False)
    protection_text = "\n".join([f"🔹 {feat['name']} — {feat['description']}" for feat in PROTECTION_DATA])
    embed.add_field(name="🛡️ Auto-Protection Features", value=protection_text, inline=False)
    embed.set_footer(text="🐈 CAT Bot • All commands are slash (/) commands")
    await interaction.response.send_message(embed=embed, ephemeral=False)

# --- TICKET COMMAND ---
@bot.tree.command(name="ticket", description="🎫 Create a support ticket")
@app_commands.default_permissions(manage_channels=True)
async def ticket_cmd(interaction: discord.Interaction, reason: str = "Support request"):
    guild = interaction.guild
    ticket_category = discord.utils.get(guild.categories, name="TICKETS")
    if not ticket_category:
        ticket_category = await guild.create_category("TICKETS")
    ticket_name = f"ticket-{interaction.user.name.lower()}-{interaction.user.discriminator}"
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }
    admin_role = discord.utils.get(guild.roles, name="Admin")
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    ticket_channel = await ticket_category.create_text_channel(ticket_name, overwrites=overwrites, topic=f"Ticket created by {interaction.user} - {reason}")
    embed = discord.Embed(title="🎫 Ticket Created", description=f"**User:** {interaction.user.mention}\n**Reason:** {reason}\n\nSupport will assist you shortly.", color=discord.Color.green(), timestamp=datetime.utcnow())
    embed.set_footer(text="To close this ticket, use /closeticket")
    await ticket_channel.send(embed=embed)
    await ticket_channel.send(f"{interaction.user.mention} - Your ticket has been created!")
    await log_action(guild, "🎫 TICKET CREATED", interaction.user, f"Reason: {reason}\nChannel: #{ticket_channel.name}")
    await interaction.response.send_message(f"✅ Ticket created! Check #{ticket_channel.name}", ephemeral=True)

# --- CLOSE TICKET COMMAND ---
@bot.tree.command(name="closeticket", description="🔒 Close a ticket channel")
@app_commands.default_permissions(manage_channels=True)
async def closeticket_cmd(interaction: discord.Interaction, reason: str = "No reason provided"):
    channel = interaction.channel
    if not channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ This is not a ticket channel.", ephemeral=True)
        return
    messages = []
    async for msg in channel.history(limit=100):
        messages.append(f"{msg.author}: {msg.content}")
    transcript = "\n".join(messages)
    await log_action(interaction.guild, "🔒 TICKET CLOSED", interaction.user, f"Reason: {reason}\nChannel: #{channel.name}")
    await interaction.response.send_message(f"🔒 Ticket closed. Reason: {reason}", ephemeral=True)
    await channel.send(f"🔒 **Ticket closed by {interaction.user.mention}**\nReason: {reason}")
    await asyncio.sleep(2)
    await channel.delete()

# --- ANNOUNCE COMMAND ---
@bot.tree.command(name="announce", description="📢 Send an announcement embed")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(channel="Channel to send announcement", title="Announcement title", message="Announcement message", color="Color (optional)")
async def announce_cmd(interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str, color: str = None):
    embed_color = discord.Color.blue()
    if color:
        try:
            embed_color = discord.Color(int(color.replace("#", ""), 16))
        except:
            pass
    embed = discord.Embed(title=title, description=message, color=embed_color, timestamp=datetime.utcnow())
    embed.set_footer(text=f"Announcement by {interaction.user}")
    await channel.send(embed=embed)
    await log_action(interaction.guild, "📢 ANNOUNCEMENT", interaction.user, f"Channel: #{channel.name}\nTitle: {title}")
    await interaction.response.send_message(f"✅ Announcement sent to #{channel.name}", ephemeral=True)

# --- POLL COMMAND ---
@bot.tree.command(name="poll", description="📊 Create a poll with reactions")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(channel="Channel to send poll", question="Poll question", option1="Option 1", option2="Option 2", option3="Option 3 (optional)", option4="Option 4 (optional)")
async def poll_cmd(interaction: discord.Interaction, channel: discord.TextChannel, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    options = [option1, option2]
    if option3:
        options.append(option3)
    if option4:
        options.append(option4)
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    poll_text = f"**{question}**\n\n"
    for i, opt in enumerate(options):
        poll_text += f"{emojis[i]} {opt}\n"
    embed = discord.Embed(title="📊 Poll", description=poll_text, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"Poll created by {interaction.user}")
    poll_msg = await channel.send(embed=embed)
    for i in range(len(options)):
        await poll_msg.add_reaction(emojis[i])
    await log_action(interaction.guild, "📊 POLL CREATED", interaction.user, f"Channel: #{channel.name}\nQuestion: {question}")
    await interaction.response.send_message(f"✅ Poll created in #{channel.name}", ephemeral=True)

# --- SLOWMODE COMMAND ---
@bot.tree.command(name="slowmode", description="⏱️ Set slowmode in a channel")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(seconds="Seconds between messages (0 to disable)", channel="Channel (default: current)")
async def slowmode_cmd(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
    target = channel or interaction.channel
    await target.edit(slowmode_delay=seconds)
    await log_action(interaction.guild, "⏱️ SLOWMODE SET", interaction.user, f"Channel: #{target.name}\nSeconds: {seconds}")
    await interaction.response.send_message(f"✅ Slowmode set to {seconds} seconds in #{target.name}", ephemeral=True)

# --- NICK COMMAND ---
@bot.tree.command(name="nick", description="✏️ Change a user's nickname")
@app_commands.default_permissions(manage_nicknames=True)
@app_commands.describe(user="The user", nickname="New nickname (leave empty to reset)")
async def nick_cmd(interaction: discord.Interaction, user: discord.Member, nickname: str = None):
    old_nick = user.display_name
    await user.edit(nick=nickname)
    await log_action(interaction.guild, "✏️ NICKNAME CHANGED", interaction.user, f"User: {user}\nOld: {old_nick}\nNew: {nickname or 'Reset'}")
    await interaction.response.send_message(f"✅ Changed nickname for {user.mention} to {nickname or 'default'}", ephemeral=True)

# --- CLEAN COMMAND ---
@bot.tree.command(name="clean", description="Deep clean chat messages (keeps files/images).")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount="Number of recent messages to check (e.g., 100, 1000)")
async def clean_channel(interaction: discord.Interaction, amount: int = 1000):
    if interaction.channel_id != CONFIG["target_channel_id"]:
        await interaction.response.send_message(f"❌ This command can only be used in <#{CONFIG['target_channel_id']}>.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(f"⏳ **Starting deep cleanup...** Scanning up to {amount} messages.", ephemeral=True)
    try:
        def is_deletable_message(msg: discord.Message) -> bool:
            if len(msg.attachments) > 0:
                return False
            if "file from" in msg.content.strip().lower():
                return False
            return True
        deleted_messages = await interaction.channel.purge(limit=amount, check=is_deletable_message)
        await interaction.followup.send(f"✅ **Cleanup Complete!** Successfully deleted {len(deleted_messages)} text messages.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Error: Bot lacks **Manage Messages** permissions.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ An error occurred while cleaning: {e}", ephemeral=True)
    except Exception as e:
        print(f"Unexpected error during clean: {e}")

# --- FORWARD FILES ONLY ---
@bot.tree.command(name="forward", description="📤 Forward ONLY videos, photos, .txt (NO XML)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(source_channel_id="ID of the channel to copy files from", target_channel="Channel to send files to", limit="Max files to copy (default 1000)")
async def forward_files_cmd(interaction: discord.Interaction, source_channel_id: str, target_channel: discord.TextChannel, limit: int = 1000):
    await interaction.response.send_message(f"📤 **Forwarding files only...**\nSource: `{source_channel_id}`\nTarget: #{target_channel.name}\nLimit: {limit}", ephemeral=True)
    try:
        file_count, skipped_count = await forward_files_only(source_channel_id, target_channel, bot.user_token, limit)
        await log_action(interaction.guild, "📤 FILES FORWARDED", interaction.user, f"Forwarded {file_count} files\nSkipped {skipped_count} files\nTo: #{target_channel.name}")
        await interaction.followup.send(f"✅ **Forward Complete!**\n📎 Forwarded: {file_count}\n🚫 Skipped: {skipped_count}\n📤 To: #{target_channel.name}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:500]}", ephemeral=True)

# --- CLONE COMMAND ---
@bot.tree.command(name="clone", description="📋 Clone server structure")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(source_id="Source server ID", target_id="Target server ID")
async def clone_cmd(interaction: discord.Interaction, source_id: str, target_id: str):
    await interaction.response.send_message("📋 Cloning...", ephemeral=True)
    try:
        src_data, src_channels = await fetch_guild_data(source_id, bot.user_token)
        target = bot.get_guild(int(target_id))
        if not target:
            await interaction.followup.send("❌ Target not found", ephemeral=True)
            return
        for ch in target.channels:
            try:
                await ch.delete()
            except:
                pass
        cat_map = {}
        for cat in [c for c in src_channels if c['type'] == 4]:
            new = await target.create_category(cat['name'], position=cat.get('position', 0))
            cat_map[cat['id']] = new
            await asyncio.sleep(0.3)
        text_count = 0
        for ch in [c for c in src_channels if c['type'] == 0]:
            parent = cat_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
            await target.create_text_channel(ch['name'], category=parent, position=ch.get('position', 0), topic=ch.get('topic', ''))
            text_count += 1
            await asyncio.sleep(0.3)
        for ch in [c for c in src_channels if c['type'] == 2]:
            parent = cat_map.get(ch.get('parent_id')) if ch.get('parent_id') else None
            await target.create_voice_channel(ch['name'], category=parent, position=ch.get('position', 0), bitrate=ch.get('bitrate', 64000))
            await asyncio.sleep(0.3)
        await interaction.followup.send(f"✅ Cloned {text_count} channels", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)

# --- BAN ---
@bot.tree.command(name="ban", description="🔨 Ban a user")
@app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def ban_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "ban", reason)
    await interaction.response.send_message(f"⚠️ Ban {user.mention}? Reason: {reason}", view=view, ephemeral=True)

# --- KICK ---
@bot.tree.command(name="kick", description="👢 Kick a user")
@app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def kick_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "kick", reason)
    await interaction.response.send_message(f"⚠️ Kick {user.mention}? Reason: {reason}", view=view, ephemeral=True)

# --- TIMEOUT ---
@bot.tree.command(name="timeout", description="⏰ Timeout a user")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="The user to timeout", minutes="Duration in minutes", reason="Reason")
async def timeout_cmd(interaction: discord.Interaction, user: discord.Member, minutes: int = 60, reason: str = "No reason"):
    await interaction.response.defer(ephemeral=True)
    await user.timeout(timedelta(minutes=minutes), reason=f"CAT: {reason}")
    await log_action(interaction.guild, "⏰ TIMEOUT", user, f"{minutes}min, Reason: {reason}")
    await interaction.followup.send(f"✅ {user} timed out for {minutes} minutes", ephemeral=True)

# --- UNTIMEOUT ---
@bot.tree.command(name="untimeout", description="⏰ Remove timeout")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="The user to untimeout")
async def untimeout_cmd(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    await user.timeout(None)
    await log_action(interaction.guild, "⏰ TIMEOUT REMOVED", user, "Timeout removed")
    await interaction.followup.send(f"✅ {user} untimed out", ephemeral=True)

# --- MUTE ---
@bot.tree.command(name="mute", description="🔇 Mute a user")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="The user to mute", reason="Reason")
async def mute_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "mute", reason)
    await interaction.response.send_message(f"⚠️ Mute {user.mention}? Reason: {reason}", view=view, ephemeral=True)

# --- UNMUTE ---
@bot.tree.command(name="unmute", description="🔊 Unmute a user")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="The user to unmute")
async def unmute_cmd(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if mute_role:
        await user.remove_roles(mute_role)
        await log_action(interaction.guild, "🔊 UNMUTED", user, "Unmuted")
        await interaction.followup.send(f"✅ {user} unmuted", ephemeral=True)
    else:
        await interaction.followup.send("❌ Muted role not found", ephemeral=True)

# --- PUNISH ---
@bot.tree.command(name="punish", description="🛡️ Choose punishment")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="The user to punish", reason="Reason")
async def punish_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = PunishmentSelect(user, interaction.guild, reason)
    await interaction.response.send_message(f"🛡️ Punish {user.mention}", view=view, ephemeral=True)

# --- PURGE ---
@bot.tree.command(name="purge", description="🧹 Delete messages")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount="Number of messages to delete", user="Filter by user (optional)")
async def purge_cmd(interaction: discord.Interaction, amount: int, user: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    def check(m): return m.author == user if user else True
    deleted = await interaction.channel.purge(limit=amount, check=check)
    await log_action(interaction.guild, "🧹 PURGE", interaction.user, f"Deleted {len(deleted)} messages")
    await interaction.followup.send(f"✅ Deleted {len(deleted)} messages", ephemeral=True)

# --- CLEAR ---
@bot.tree.command(name="clear", description="🧹 DELETE ALL messages")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel to clear (leave blank for current)")
async def clear_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target = channel or interaction.channel
    view = ClearConfirmView(target, interaction.guild, interaction.user)
    await interaction.response.send_message(f"⚠️ Delete ALL messages in #{target.name}?", view=view, ephemeral=True)

# --- DELETE TEXT ---
@bot.tree.command(name="deletetext", description="🗑️ Delete ONLY text (keep files)")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel to clean", limit="Max messages to check")
async def deletetext_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None, limit: int = 1000):
    target = channel or interaction.channel
    view = DeleteTextConfirmView(target, interaction.guild, interaction.user, limit)
    await interaction.response.send_message(f"⚠️ Delete text in #{target.name}?", view=view, ephemeral=True)

# --- DELETE FILES ---
@bot.tree.command(name="deletefiles", description="🗑️ Delete ONLY files (keep text)")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel to clean", limit="Max messages to check")
async def deletefiles_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None, limit: int = 1000):
    target = channel or interaction.channel
    view = DeleteFilesConfirmView(target, interaction.guild, interaction.user, limit)
    await interaction.response.send_message(f"⚠️ Delete files in #{target.name}?", view=view, ephemeral=True)

# --- DELETE ALL CHANNELS ---
@bot.tree.command(name="deleteallchannels", description="💀 DELETE ALL channels")
@app_commands.default_permissions(administrator=True)
async def deleteall_cmd(interaction: discord.Interaction):
    view = DeleteAllConfirmView(interaction.guild, interaction.user)
    await interaction.response.send_message("💀 Delete ALL channels?", view=view, ephemeral=True)

# --- LOCKDOWN ---
@bot.tree.command(name="lockdown", description="🔒 Lock server")
@app_commands.default_permissions(administrator=True)
async def lockdown_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    for ch in interaction.guild.channels:
        if isinstance(ch, discord.TextChannel):
            await ch.set_permissions(interaction.guild.default_role, send_messages=False)
    await log_action(interaction.guild, "🔒 LOCKDOWN", interaction.user, "Server locked")
    await interaction.followup.send("🔒 Server locked", ephemeral=True)

# --- UNLOCK ---
@bot.tree.command(name="unlock", description="🔓 Unlock server")
@app_commands.default_permissions(administrator=True)
async def unlock_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    for ch in interaction.guild.channels:
        if isinstance(ch, discord.TextChannel):
            await ch.set_permissions(interaction.guild.default_role, send_messages=None)
    await log_action(interaction.guild, "🔓 UNLOCKED", interaction.user, "Server unlocked")
    await interaction.followup.send("🔓 Server unlocked", ephemeral=True)

# --- LOCK ALL ---
@bot.tree.command(name="lockall", description="🔒 Lock ALL channels")
@app_commands.default_permissions(administrator=True)
async def lockall_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for ch in interaction.guild.channels:
        try:
            if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
                await ch.set_permissions(interaction.guild.default_role, send_messages=False, connect=False, speak=False)
                count += 1
                await asyncio.sleep(0.2)
        except:
            pass
    await log_action(interaction.guild, "🔒 LOCKALL", interaction.user, f"Locked {count} channels")
    await interaction.followup.send(f"🔒 Locked {count} channels", ephemeral=True)

# --- UNLOCK ALL ---
@bot.tree.command(name="unlockall", description="🔓 Unlock ALL channels")
@app_commands.default_permissions(administrator=True)
async def unlockall_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for ch in interaction.guild.channels:
        try:
            if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
                await ch.set_permissions(interaction.guild.default_role, send_messages=None, connect=None, speak=None)
                count += 1
                await asyncio.sleep(0.2)
        except:
            pass
    await log_action(interaction.guild, "🔓 UNLOCKALL", interaction.user, f"Unlocked {count} channels")
    await interaction.followup.send(f"🔓 Unlocked {count} channels", ephemeral=True)

# --- REMOVE ROLES ---
@bot.tree.command(name="removeroles", description="⚔️ Remove all roles")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="The user to strip roles from", reason="Reason")
async def removeroles_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "remove_roles", reason)
    await interaction.response.send_message(f"⚠️ Remove roles from {user.mention}?", view=view, ephemeral=True)

# --- SETUP ---
@bot.tree.command(name="setup", description="🔧 Setup logs channel")
@app_commands.default_permissions(administrator=True)
async def setup_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await setup_logs_channel(interaction.guild)
    await interaction.followup.send("✅ Logs channel created", ephemeral=True)

# --- STATS ---
@bot.tree.command(name="stats", description="📊 Server stats")
@app_commands.default_permissions(administrator=True)
async def stats_cmd(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"📊 Server Stats - {guild.name}", color=discord.Color.blue())
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="📁 Categories", value=len(guild.categories), inline=True)
    embed.add_field(name="🔊 Voice", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="📝 Text", value=len(guild.text_channels), inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- CONTEXT MENUS ---
@bot.tree.context_menu(name="🔨 Ban User")
@app_commands.default_permissions(ban_members=True)
async def context_ban(interaction: discord.Interaction, user: discord.Member):
    view = ConfirmView(user, interaction.guild, "ban", "Context menu")
    await interaction.response.send_message(f"⚠️ Ban {user.mention}?", view=view, ephemeral=True)

@bot.tree.context_menu(name="👢 Kick User")
@app_commands.default_permissions(kick_members=True)
async def context_kick(interaction: discord.Interaction, user: discord.Member):
    view = ConfirmView(user, interaction.guild, "kick", "Context menu")
    await interaction.response.send_message(f"⚠️ Kick {user.mention}?", view=view, ephemeral=True)

@bot.tree.context_menu(name="⏰ Timeout User (60min)")
@app_commands.default_permissions(moderate_members=True)
async def context_timeout(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    await user.timeout(timedelta(minutes=60), reason="Context menu")
    await log_action(interaction.guild, "⏰ TIMEOUT", user, "60min via context menu")
    await interaction.followup.send(f"✅ {user} timed out for 60 minutes", ephemeral=True)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Web server started in background")
    bot.run(os.environ.get("DISCORD_TOKEN"))
