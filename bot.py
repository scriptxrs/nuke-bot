# ============================================================
# KERS0NE BOT — COMPLETE WITH WEBSITE
# ============================================================

import os
import asyncio
import aiohttp
import io
import re
import time
import zipfile
import threading
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session

import discord
from discord import Intents, Embed, Color, File, Member, TextChannel, app_commands, ui, ButtonStyle
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput

# ============================================================
# FLASK WEB APP
# ============================================================
flask_app = Flask(__name__)
flask_app.secret_key = os.environ.get("SESSION_SECRET", "kers0ne_secret_key_2026")

COMMANDS_LIST = [
    {"category": "🛡️ Moderation", "commands": ["/ban", "/kick", "/timeout", "/untimeout", "/mute", "/unmute", "/punish", "/removeroles", "/nick", "/slowmode", "/warn", "/warnings", "/clearwarnings"]},
    {"category": "🔒 Channel Lock", "commands": ["/lock", "/unlock", "/lockall", "/unlockall"]},
    {"category": "🧹 Cleanup", "commands": ["/purge", "/clear", "/deletetext", "/deletefiles"]},
    {"category": "📤 Forward", "commands": ["/forward", "/forward2", "/forward3"]},
    {"category": "🔒 Server Control", "commands": ["/lockdown", "/unlockserver", "/deleteallchannels"]},
    {"category": "🎫 Tickets", "commands": ["/ticket", "/ticketsetup", "/closeticket"]},
    {"category": "🌐 Webhooks", "commands": ["/create-webhook", "/spam-webhook", "/delete-webhook", "/spam-multi"]},
    {"category": "📝 Embeds", "commands": ["/create-embed", "/embed"]},
    {"category": "📢 Utility", "commands": ["/help", "/announce", "/poll", "/setup", "/stats", "/say", "/dm"]},
    {"category": "👑 Admin", "commands": ["/give-admin", "/mass-admin", "/remove-admin"]},
    {"category": "📋 Clone", "commands": ["/clone"]},
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kers0ne Bot — Command List</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid rgba(255,255,255,0.05);
            margin-bottom: 40px;
        }
        .header h1 { font-size: 3.5rem; color: #fff; }
        .header h1 span { color: #6366f1; }
        .header p { color: #888; margin-top: 10px; }
        .status {
            display: inline-block;
            background: rgba(0,255,0,0.1);
            color: #0f0;
            padding: 8px 20px;
            border-radius: 20px;
            margin-top: 15px;
            border: 1px solid rgba(0,255,0,0.2);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .stat-card .number { font-size: 2.5rem; font-weight: bold; color: #6366f1; }
        .stat-card .label { color: #666; margin-top: 5px; }
        .category {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
        }
        .category-title {
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: #fff;
        }
        .category-title span {
            font-size: 0.9rem;
            color: #666;
            background: rgba(255,255,255,0.05);
            padding: 3px 12px;
            border-radius: 12px;
            margin-left: 10px;
        }
        .command-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
        }
        .command-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.95rem;
            color: #ccc;
            transition: all 0.3s;
        }
        .command-item:hover {
            background: rgba(99,102,241,0.1);
            border-color: #6366f1;
            color: #fff;
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            padding: 30px 0;
            color: #444;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 40px;
        }
        .footer a { color: #6366f1; text-decoration: none; }
        @media (max-width: 600px) {
            .header h1 { font-size: 2rem; }
            .command-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>⚫ Kers0ne <span>Bot</span></h1>
        <p>Ultimate Discord Security & Utility Bot</p>
        <div class="status">🟢 Online • {{ time }}</div>
    </div>
    <div class="stats">
        <div class="stat-card"><div class="number">{{ total_commands }}</div><div class="label">Total Commands</div></div>
        <div class="stat-card"><div class="number">{{ categories }}</div><div class="label">Categories</div></div>
        <div class="stat-card"><div class="number">🟢</div><div class="label">Status</div></div>
        <div class="stat-card"><div class="number">⚡</div><div class="label">Fast & Secure</div></div>
    </div>
    {% for cat in commands %}
    <div class="category">
        <div class="category-title">{{ cat.category }} <span>{{ cat.commands|length }} commands</span></div>
        <div class="command-grid">
            {% for cmd in cat.commands %}
            <div class="command-item">{{ cmd }}</div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
    <div class="footer">
        ⚫ Kers0ne Bot • Built with ❤️ • <a href="https://discord.com/oauth2/authorize?client_id={{ client_id }}&permissions=8&scope=bot">Invite Bot</a>
    </div>
</div>
</body>
</html>"""

@flask_app.route('/')
def index():
    total = sum(len(cat['commands']) for cat in COMMANDS_LIST)
    return render_template_string(
        HTML_TEMPLATE,
        commands=COMMANDS_LIST,
        total_commands=total,
        categories=len(COMMANDS_LIST),
        client_id=os.environ.get("CLIENT_ID", ""),
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@flask_app.route('/health')
def health():
    return jsonify({"status": "online", "timestamp": datetime.now().isoformat()})

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ============================================================
# DISCORD BOT CONFIG
# ============================================================
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# ============================================================
# BOT SETUP
# ============================================================
intents = Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# DATA STORAGE
# ============================================================
warnings_db = {}
join_timestamps = {}
message_cache = {}
deletion_cache = {}

CONFIG = {
    "max_joins_per_minute": 5,
    "max_messages_per_second": 10,
    "max_mentions_per_message": 5,
    "max_new_account_age_hours": 24,
    "default_punishment": "ban",
    "log_channel_name": "kers0ne-logs"
}

# ============================================================
# LOGGING
# ============================================================
async def setup_logs_channel(guild):
    log_channel = discord.utils.get(guild.channels, name=CONFIG["log_channel_name"])
    if not log_channel:
        category = discord.utils.get(guild.categories, name="KERS0NE SECURITY")
        if not category:
            category = await guild.create_category("KERS0NE SECURITY")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        log_channel = await guild.create_text_channel(CONFIG["log_channel_name"], category=category, overwrites=overwrites)
        await log_channel.send("🔒 **KERS0NE SECURITY INITIALIZED**")
    return log_channel

async def log_action(guild, action, user, details=""):
    log_channel = discord.utils.get(guild.channels, name=CONFIG["log_channel_name"])
    if not log_channel:
        log_channel = await setup_logs_channel(guild)
    embed = Embed(
        title=f"🔒 {action}",
        description=f"**User:** {user.mention} (`{user.id}`)\n{details}",
        color=Color.dark_gray(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Kers0ne Security • {guild.name}")
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
            await guild.ban(user, reason=f"Kers0ne: {reason}")
            await log_action(guild, "🔨 BANNED", user, f"Reason: {reason}")
            return "banned"
        elif punishment == "kick":
            await guild.kick(user, reason=f"Kers0ne: {reason}")
            await log_action(guild, "👢 KICKED", user, f"Reason: {reason}")
            return "kicked"
        elif punishment == "timeout":
            await user.timeout(timedelta(minutes=60), reason=f"Kers0ne: {reason}")
            await log_action(guild, "⏰ TIMEOUT", user, f"60 minutes. Reason: {reason}")
            return "timed out"
        elif punishment == "mute":
            mute_role = discord.utils.get(guild.roles, name="Muted")
            if not mute_role:
                mute_role = await guild.create_role(name="Muted", permissions=discord.Permissions(0))
                for channel in guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
            await user.add_roles(mute_role, reason=f"Kers0ne: {reason}")
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
# DOWNLOAD HELPERS
# ============================================================
async def download_file(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            return None

async def fetch_guild_data(guild_id, token):
    headers = {"Authorization": f"Bot {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}", headers=headers) as resp:
            guild = await resp.json() if resp.status == 200 else {}
        async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers) as resp:
            channels = await resp.json() if resp.status == 200 else []
        async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers=headers) as resp:
            roles = await resp.json() if resp.status == 200 else []
        return guild, channels, roles

# ============================================================
# WEBSITE DOWNLOADER FOR FORWARD3
# ============================================================
def fix_url(match, base_url, current_url):
    attr = match.group(1)
    url_value = match.group(2)
    if url_value.startswith('http') or url_value.startswith('//'):
        return f'{attr}="{url_value}"'
    full_url = urljoin(current_url, url_value)
    return f'{attr}="{full_url}"'

def fix_css_url(match, base_url, current_url):
    url_value = match.group(1)
    if url_value.startswith('http') or url_value.startswith('//'):
        return f'url("{url_value}")'
    full_url = urljoin(current_url, url_value)
    return f'url("{full_url}")'

async def download_website_real(base_url, max_pages=50):
    visited = set()
    to_visit = [base_url]
    files = {}
    file_count = 0
    page_count = 0
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    async with aiohttp.ClientSession() as session:
        while to_visit and page_count < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)
            
            try:
                async with session.get(current_url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }) as resp:
                    if resp.status != 200:
                        continue
                    
                    content = await resp.read()
                    content_type = resp.headers.get('content-type', '').lower()
                    parsed = urlparse(current_url)
                    path = parsed.path or '/index.html'
                    
                    if 'text/html' in content_type:
                        page_count += 1
                        try:
                            html = content.decode('utf-8', errors='ignore')
                            html = re.sub(r'(href|src)=["\']/([^"\']+)["\']', f'\\1="{base_url}/\\2"', html)
                            html = re.sub(r'(href|src)=["\']([^"\']+)["\']', lambda m: fix_url(m, base_url, current_url), html)
                            
                            link_pattern = r'(?:href|src)=["\']([^"\']+)["\']'
                            for match in re.finditer(link_pattern, html):
                                link = match.group(1)
                                if link.startswith('#') or link.startswith('javascript:') or link.startswith('mailto:') or link.startswith('tel:'):
                                    continue
                                full_url = urljoin(current_url, link)
                                if full_url.startswith(base_url) and full_url not in visited:
                                    to_visit.append(full_url)
                            
                            if path.endswith('/') or not path.split('/')[-1].count('.'):
                                path += 'index.html'
                            elif not any(path.endswith(ext) for ext in ['.html', '.htm']):
                                path += '.html'
                            
                            files[path] = html.encode('utf-8')
                            file_count += 1
                        except:
                            files[path] = content
                            file_count += 1
                    
                    elif 'text/css' in content_type:
                        try:
                            css = content.decode('utf-8', errors='ignore')
                            css = re.sub(r'url\(["\']?([^"\'\)]+)["\']?\)', lambda m: fix_css_url(m, base_url, current_url), css)
                            files[path if path.endswith('.css') else path + '.css'] = css.encode('utf-8')
                            file_count += 1
                        except:
                            files[path if path.endswith('.css') else path + '.css'] = content
                            file_count += 1
                    
                    elif 'javascript' in content_type or 'ecmascript' in content_type:
                        try:
                            js = content.decode('utf-8', errors='ignore')
                            files[path if path.endswith('.js') else path + '.js'] = js.encode('utf-8')
                            file_count += 1
                        except:
                            files[path if path.endswith('.js') else path + '.js'] = content
                            file_count += 1
                    
                    elif 'image/' in content_type:
                        ext = content_type.split('/')[-1].split(';')[0]
                        if ext in ['jpeg', 'png', 'gif', 'webp', 'svg+xml', 'bmp', 'ico']:
                            if ext == 'svg+xml':
                                ext = 'svg'
                            elif ext == 'jpeg':
                                ext = 'jpg'
                            filename = path.split('/')[-1]
                            if not filename or '.' not in filename:
                                filename = f"image_{file_count}.{ext}"
                            files[filename] = content
                            file_count += 1
                    else:
                        filename = path.split('/')[-1] or f"file_{file_count}"
                        files[filename] = content
                        file_count += 1
                    
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"Error downloading {current_url}: {e}")
                continue
    
    if not files:
        return None, 0, 0
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for path, content in files.items():
            clean_path = path.lstrip('/')
            if not clean_path:
                clean_path = 'index.html'
            zip_file.writestr(clean_path, content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue(), file_count, page_count

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

    @discord.ui.button(label="✅ Confirm", style=ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.confirmed = True
        self.stop()
        result = await punish_user(self.user, self.guild, self.reason, self.action)
        await interaction.followup.send(f"✅ **{self.user}** has been {result}.", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=ButtonStyle.red)
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

    @discord.ui.button(label="💀 YES, DELETE ALL CHANNELS", style=ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        self.confirmed = True
        self.stop()
        deleted = 0
        failed = 0
        for channel in self.guild.channels:
            try:
                await channel.delete()
                deleted += 1
                await asyncio.sleep(0.3)
            except:
                failed += 1
        try:
            new_channel = await self.guild.create_text_channel("☠️-reset-by-kers0ne")
            await new_channel.send(f"💀 **ALL CHANNELS DELETED!**\n🗑️ Deleted: {deleted}\n❌ Failed: {failed}")
        except:
            pass
        await log_action(self.guild, "💀 ALL CHANNELS DELETED", self.user, f"Deleted {deleted}, failed {failed}")
        await interaction.followup.send(f"✅ **Deleted {deleted} channels**\n❌ Failed: {failed}", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=ButtonStyle.secondary)
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

    @discord.ui.button(label="💀 YES, DELETE ALL", style=ButtonStyle.danger)
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

    @discord.ui.button(label="❌ Cancel", style=ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.confirmed = False
        self.stop()

class EmbedModal(Modal, title="Create Embed"):
    title_input = TextInput(label="Title", placeholder="Enter embed title...", required=False)
    description_input = TextInput(label="Description", placeholder="Enter embed description...", style=discord.TextStyle.paragraph, required=False)
    color_input = TextInput(label="Color (hex)", placeholder="#000000 or random", required=False)
    footer_input = TextInput(label="Footer", placeholder="Enter footer text...", required=False)
    image_input = TextInput(label="Image URL", placeholder="https://example.com/image.png", required=False)
    thumbnail_input = TextInput(label="Thumbnail URL", placeholder="https://example.com/thumb.png", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        embed = Embed()
        if self.title_input.value:
            embed.title = self.title_input.value
        if self.description_input.value:
            embed.description = self.description_input.value
        if self.color_input.value:
            try:
                if self.color_input.value.lower() == "random":
                    embed.color = Color.random()
                else:
                    embed.color = Color(int(self.color_input.value.replace("#", ""), 16))
            except:
                embed.color = Color.dark_gray()
        if self.footer_input.value:
            embed.set_footer(text=self.footer_input.value)
        if self.image_input.value:
            embed.set_image(url=self.image_input.value)
        if self.thumbnail_input.value:
            embed.set_thumbnail(url=self.thumbnail_input.value)
        embed.timestamp = datetime.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=False)
        await log_action(interaction.guild, "📝 EMBED CREATED", interaction.user, f"Title: {self.title_input.value or 'None'}")

class TicketButtonView(View):
    @discord.ui.button(label="🎫 Create Ticket", style=ButtonStyle.primary, custom_id="create_ticket")
    async def ticket_button(self, interaction: discord.Interaction, button: Button):
        ticket_category = discord.utils.get(interaction.guild.categories, name="TICKETS")
        if not ticket_category:
            ticket_category = await interaction.guild.create_category("TICKETS")
        
        for ch in ticket_category.channels:
            if ch.name.startswith(f"ticket-{interaction.user.name.lower()}"):
                await interaction.response.send_message("❌ You already have an open ticket!", ephemeral=True)
                return
        
        ticket_name = f"ticket-{interaction.user.name.lower()}"
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        ticket_channel = await ticket_category.create_text_channel(ticket_name, overwrites=overwrites)
        ticket_embed = Embed(
            title="🎫 Ticket Created",
            description=f"**User:** {interaction.user.mention}\nSupport will assist you shortly.\n\nTo close, use `/closeticket`",
            color=Color.dark_gray(),
            timestamp=datetime.utcnow()
        )
        await ticket_channel.send(embed=ticket_embed)
        await ticket_channel.send(f"{interaction.user.mention} - Your ticket has been created!")
        await log_action(interaction.guild, "🎫 TICKET CREATED", interaction.user, f"Channel: #{ticket_channel.name}")
        await interaction.response.send_message(f"✅ Ticket created! Check #{ticket_channel.name}", ephemeral=True)

# ============================================================
# COMMANDS — ALL 50+ COMMANDS
# ============================================================

# --- HELP ---
@bot.tree.command(name="help", description="📋 Show all available commands")
async def help_cmd(interaction: discord.Interaction):
    embed = Embed(
        title="⚫ Kers0ne Bot - Command List",
        description="Here are all available commands. Use `/` to see them in Discord.",
        color=Color.dark_gray(),
        timestamp=datetime.utcnow()
    )
    commands_list = [
        ("🛡️ Moderation", "/ban, /kick, /timeout, /untimeout, /mute, /unmute, /punish, /removeroles, /nick, /slowmode, /warn, /warnings, /clearwarnings"),
        ("🔒 Channel Lock", "/lock, /unlock, /lockall, /unlockall"),
        ("🧹 Cleanup", "/purge, /clear, /deletetext, /deletefiles"),
        ("📤 Forward", "/forward, /forward2, /forward3"),
        ("🔒 Server Control", "/lockdown, /unlockserver, /deleteallchannels"),
        ("🎫 Tickets", "/ticket, /ticketsetup, /closeticket"),
        ("🌐 Webhooks", "/create-webhook, /spam-webhook, /delete-webhook, /spam-multi"),
        ("📝 Embeds", "/create-embed, /embed"),
        ("📢 Utility", "/announce, /poll, /setup, /stats, /say, /dm"),
        ("👑 Admin", "/give-admin, /mass-admin, /remove-admin"),
        ("📋 Clone", "/clone")
    ]
    for name, cmds in commands_list:
        embed.add_field(name=name, value=cmds, inline=False)
    embed.set_footer(text="⚫ Kers0ne Bot • All commands are slash (/) commands")
    await interaction.response.send_message(embed=embed, ephemeral=False)

# --- FORWARD (FILES) ---
@bot.tree.command(name="forward", description="📤 Forward ALL files from ANY channel")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    source_channel_id="Channel ID to copy from",
    target_channel="Channel to send to",
    limit="Max files to copy (default 1000)"
)
async def forward_files_cmd(
    interaction: discord.Interaction,
    source_channel_id: str,
    target_channel: discord.TextChannel,
    limit: int = 1000
):
    await interaction.response.send_message(f"📤 Forwarding files from `{source_channel_id}`...", ephemeral=True)
    try:
        messages = []
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
            async with session.get(f"https://discord.com/api/v10/channels/{source_channel_id}", headers=headers) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Cannot access channel!", ephemeral=True)
                    return
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
                    await asyncio.sleep(0.05)
        if not messages:
            await interaction.followup.send("❌ No messages found!", ephemeral=True)
            return
        file_count = 0
        for msg in messages:
            attachments = msg.get('attachments', [])
            if not attachments:
                continue
            author_name = msg['author']['username']
            author_id = msg['author']['id']
            timestamp = msg.get('timestamp', '')[:19]
            await target_channel.send(f"📎 **{author_name}** (`{author_id}`) [{timestamp}]")
            for att in attachments:
                try:
                    file_data = await download_file(att['url'])
                    if file_data:
                        await target_channel.send(file=discord.File(io.BytesIO(file_data), filename=att['filename']))
                        file_count += 1
                        await asyncio.sleep(0.1)
                except:
                    pass
        await log_action(interaction.guild, "📤 FILES FORWARDED", interaction.user, f"Forwarded {file_count} files")
        await interaction.followup.send(f"✅ Forwarded {file_count} files to #{target_channel.name}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:500]}", ephemeral=True)

# --- FORWARD2 (LOADSTRINGS) ---
@bot.tree.command(name="forward2", description="📤 Forward ALL loadstrings from ANY channel")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    source_channel_id="Channel ID to scan",
    target_channel="Channel to send to",
    limit="Max messages to scan"
)
async def forward_loadstrings_cmd(
    interaction: discord.Interaction,
    source_channel_id: str,
    target_channel: discord.TextChannel,
    limit: int = 1000
):
    await interaction.response.send_message(f"📤 Scanning for loadstrings in `{source_channel_id}`...", ephemeral=True)
    try:
        messages = []
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
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
                    await asyncio.sleep(0.05)
        if not messages:
            await interaction.followup.send("❌ No messages found!", ephemeral=True)
            return
        loadstrings = []
        patterns = [r'loadstring\(game:HttpGet\("([^"]+)"\)\)\(\)', r'loadstring\("([^"]+)"\)\(\)', r'loadstring\(game:HttpGet\("([^"]+)"\)', r'loadstring\("([^"]+)"\)', r'loadstring\(([^)]+)\)']
        for msg in messages:
            content = msg.get('content', '')
            if not content:
                continue
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    for match in matches:
                        loadstrings.append({'author': msg['author']['username'], 'author_id': msg['author']['id'], 'timestamp': msg.get('timestamp', '')[:19], 'loadstring': match if isinstance(match, str) else str(match)})
        if not loadstrings:
            await interaction.followup.send("❌ No loadstrings found!", ephemeral=True)
            return
        await target_channel.send(f"📤 **LOADSTRINGS FOUND:** {len(loadstrings)}")
        for ls in loadstrings[:50]:
            embed = Embed(title="🔗 Loadstring", color=Color.dark_gray(), timestamp=datetime.utcnow())
            embed.add_field(name="Author", value=f"{ls['author']} (`{ls['author_id']}`)", inline=True)
            embed.add_field(name="Time", value=ls['timestamp'], inline=True)
            embed.add_field(name="Loadstring", value=f"```lua\n{ls['loadstring'][:300]}\n```", inline=False)
            await target_channel.send(embed=embed)
            await asyncio.sleep(0.1)
        await log_action(interaction.guild, "📤 LOADSTRINGS FORWARDED", interaction.user, f"Found {len(loadstrings)}")
        await interaction.followup.send(f"✅ Found {len(loadstrings)} loadstrings", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:500]}", ephemeral=True)

# --- FORWARD3 (WEBSITE DOWNLOADER) ---
@bot.tree.command(name="forward3", description="📦 Download a website and zip all files")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(url="Website URL", target_channel="Channel to send ZIP", max_pages="Max pages to crawl")
async def forward_website_cmd(
    interaction: discord.Interaction,
    url: str,
    target_channel: discord.TextChannel,
    max_pages: int = 50
):
    await interaction.response.send_message(f"📦 Downloading website {url}...", ephemeral=True)
    try:
        await interaction.followup.send("🌐 Crawling website...", ephemeral=True)
        zip_data, file_count, page_count = await download_website_real(url, max_pages)
        if not zip_data or file_count == 0:
            await interaction.followup.send("❌ Failed to download website!", ephemeral=True)
            return
        zip_file = discord.File(io.BytesIO(zip_data), filename=f"website_backup_{int(time.time())}.zip")
        await target_channel.send(f"📦 **Website Downloaded!**\n🌐 {url}\n📄 Pages: {page_count}\n📁 Files: {file_count}", file=zip_file)
        await log_action(interaction.guild, "📦 WEBSITE DOWNLOADED", interaction.user, f"URL: {url}\nPages: {page_count}\nFiles: {file_count}")
        await interaction.followup.send(f"✅ Download Complete!\n📄 Pages: {page_count}\n📁 Files: {file_count}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:500]}", ephemeral=True)

# --- CLONE ---
@bot.tree.command(name="clone", description="📋 Clone server structure + roles")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(source_id="Source server ID", target_id="Target server ID")
async def clone_cmd(interaction: discord.Interaction, source_id: str, target_id: str):
    await interaction.response.send_message(f"📋 Cloning {source_id} → {target_id}...", ephemeral=True)
    try:
        guild_data, channels_data, roles_data = await fetch_guild_data(source_id, DISCORD_TOKEN)
        if not guild_data:
            await interaction.edit_original_response(content="❌ Failed to fetch source server.")
            return
        target = bot.get_guild(int(target_id))
        if not target:
            await interaction.edit_original_response(content="❌ Target server not found!")
            return
        if not target.me.guild_permissions.manage_channels or not target.me.guild_permissions.manage_roles:
            await interaction.edit_original_response(content="❌ I need Manage Channels and Manage Roles permissions!")
            return
        for channel in target.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.2)
            except:
                pass
        role_map = {}
        for role in roles_data:
            if role['name'] == '@everyone':
                continue
            try:
                new_role = await target.create_role(name=role['name'], permissions=discord.Permissions(role['permissions']), color=discord.Color(role['color']) if role.get('color') else discord.Color.default(), hoist=role.get('hoist', False), mentionable=role.get('mentionable', False))
                role_map[role['id']] = new_role
                await asyncio.sleep(0.3)
            except:
                pass
        cat_map = {}
        for cat in [c for c in channels_data if c['type'] == 4]:
            try:
                new_cat = await target.create_category(cat['name'])
                cat_map[cat['id']] = new_cat
                await asyncio.sleep(0.3)
            except:
                pass
        for ch in [c for c in channels_data if c['type'] == 0]:
            try:
                await target.create_text_channel(ch['name'], category=cat_map.get(ch.get('parent_id')))
                await asyncio.sleep(0.3)
            except:
                pass
        for ch in [c for c in channels_data if c['type'] == 2]:
            try:
                await target.create_voice_channel(ch['name'], category=cat_map.get(ch.get('parent_id')))
                await asyncio.sleep(0.3)
            except:
                pass
        await log_action(interaction.guild, "📋 CLONE COMPLETE", interaction.user, f"Source: {guild_data.get('name', 'Unknown')}\nTarget: {target.name}")
        await interaction.edit_original_response(content=f"✅ Clone Complete!\n📊 {guild_data.get('name', 'Unknown')} → {target.name}")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)[:500]}")

# --- GIVE ADMIN ---
@bot.tree.command(name="give-admin", description="👑 Give yourself Administrator")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="User to give admin")
async def give_admin_cmd(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    if not interaction.guild.me.guild_permissions.administrator:
        await interaction.response.send_message("❌ I need Administrator permissions!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        admin_role = discord.utils.get(interaction.guild.roles, name="Kers0ne-Admin")
        if not admin_role:
            admin_role = await interaction.guild.create_role(name="Kers0ne-Admin", permissions=discord.Permissions.all(), color=Color.dark_gray(), hoist=True)
            await interaction.guild.me.add_roles(admin_role)
        await target.add_roles(admin_role)
        await log_action(interaction.guild, "👑 ADMIN GRANTED", target, f"By: {interaction.user}")
        await interaction.followup.send(f"✅ {target.mention} now has Administrator!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)

# --- MASS ADMIN ---
@bot.tree.command(name="mass-admin", description="👑 Give Administrator to EVERYONE")
@app_commands.default_permissions(administrator=True)
async def mass_admin_cmd(interaction: discord.Interaction):
    if not interaction.guild.me.guild_permissions.administrator:
        await interaction.response.send_message("❌ I need Administrator permissions!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        admin_role = discord.utils.get(interaction.guild.roles, name="Kers0ne-Admin")
        if not admin_role:
            admin_role = await interaction.guild.create_role(name="Kers0ne-Admin", permissions=discord.Permissions.all(), color=Color.dark_gray(), hoist=True)
            await interaction.guild.me.add_roles(admin_role)
        count = 0
        for member in interaction.guild.members:
            if member == interaction.guild.me:
                continue
            try:
                await member.add_roles(admin_role)
                count += 1
                await asyncio.sleep(0.1)
            except:
                pass
        await log_action(interaction.guild, "👑 MASS ADMIN", interaction.user, f"Gave admin to {count} members")
        await interaction.followup.send(f"✅ Gave Administrator to {count} members!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)

# --- REMOVE ADMIN ---
@bot.tree.command(name="remove-admin", description="👑 Remove Administrator")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="User to remove admin from")
async def remove_admin_cmd(interaction: discord.Interaction, user: discord.Member):
    admin_role = discord.utils.get(interaction.guild.roles, name="Kers0ne-Admin")
    if not admin_role:
        await interaction.response.send_message("❌ No admin role found.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        await user.remove_roles(admin_role)
        await log_action(interaction.guild, "👑 ADMIN REMOVED", user, f"By: {interaction.user}")
        await interaction.followup.send(f"✅ Removed Admin from {user.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)

# --- WEBHOOK COMMANDS ---
@bot.tree.command(name="spam-webhook", description="🌐 ULTRA FAST webhook spam")
@app_commands.default_permissions(manage_webhooks=True)
@app_commands.describe(webhook_url="Webhook URL", message="Message to spam", count="Number of messages")
async def spam_webhook_cmd(interaction: discord.Interaction, webhook_url: str, message: str, count: int = 100):
    await interaction.response.defer(ephemeral=True)
    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        await interaction.followup.send("❌ Invalid webhook URL!", ephemeral=True)
        return
    await interaction.followup.send(f"🌐 SPAM STARTED! Count: {count}", ephemeral=True)
    asyncio.create_task(spam_webhook_task(webhook_url, message, count, interaction))

async def spam_webhook_task(webhook_url, message, count, interaction):
    sent = 0
    failed = 0
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        data = {"content": message}
        for _ in range(count):
            try:
                async with session.post(webhook_url, json=data) as resp:
                    if resp.status in [200, 204]:
                        sent += 1
                    else:
                        failed += 1
            except:
                failed += 1
    elapsed = time.time() - start_time
    speed = sent / elapsed if elapsed > 0 else 0
    try:
        await interaction.user.send(f"✅ SPAM COMPLETE!\n📤 Sent: {sent}\n❌ Failed: {failed}\n⏱️ {elapsed:.2f}s\n🚀 {speed:.0f} msg/s")
    except:
        pass

@bot.tree.command(name="spam-multi", description="🌐 Spam using MULTIPLE webhooks")
@app_commands.default_permissions(manage_webhooks=True)
@app_commands.describe(webhook_urls="Comma-separated URLs", message="Message", count_per_webhook="Messages per webhook")
async def spam_multi_cmd(interaction: discord.Interaction, webhook_urls: str, message: str, count_per_webhook: int = 100):
    await interaction.response.defer(ephemeral=True)
    urls = [url.strip() for url in webhook_urls.split(",") if url.strip()]
    if not urls:
        await interaction.followup.send("❌ No valid webhook URLs!", ephemeral=True)
        return
    await interaction.followup.send(f"🌐 MULTI SPAM! {len(urls)} webhooks", ephemeral=True)
    tasks = [spam_webhook_task_quick(url, message, count_per_webhook) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_sent = sum(r[0] if isinstance(r, tuple) else 0 for r in results if isinstance(r, tuple))
    total_failed = sum(r[1] if isinstance(r, tuple) else 0 for r in results if isinstance(r, tuple))
    await interaction.followup.send(f"✅ MULTI SPAM!\n📤 Sent: {total_sent}\n❌ Failed: {total_failed}", ephemeral=True)

async def spam_webhook_task_quick(webhook_url, message, count):
    sent = 0
    failed = 0
    async with aiohttp.ClientSession() as session:
        data = {"content": message}
        for _ in range(count):
            try:
                async with session.post(webhook_url, json=data) as resp:
                    if resp.status in [200, 204]:
                        sent += 1
                    else:
                        failed += 1
            except:
                failed += 1
    return sent, failed

@bot.tree.command(name="create-webhook", description="🌐 Create a webhook")
@app_commands.default_permissions(manage_webhooks=True)
@app_commands.describe(channel="Channel", name="Webhook name", avatar="Avatar URL")
async def create_webhook_cmd(interaction: discord.Interaction, channel: discord.TextChannel, name: str, avatar: str = None):
    await interaction.response.defer(ephemeral=True)
    try:
        webhook = await channel.create_webhook(name=name, avatar=avatar)
        await log_action(interaction.guild, "🌐 WEBHOOK CREATED", interaction.user, f"Name: {name}\nChannel: #{channel.name}")
        await interaction.followup.send(f"✅ Webhook created!\n**URL:** `{webhook.url}`", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="delete-webhook", description="🌐 Delete a webhook")
@app_commands.default_permissions(manage_webhooks=True)
@app_commands.describe(webhook_url="Webhook URL")
async def delete_webhook_cmd(interaction: discord.Interaction, webhook_url: str):
    await interaction.response.defer(ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(webhook_url) as resp:
                if resp.status in [200, 204]:
                    await log_action(interaction.guild, "🌐 WEBHOOK DELETED", interaction.user, f"URL: {webhook_url[:50]}...")
                    await interaction.followup.send("✅ Webhook deleted!", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed. Status: {resp.status}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)

# --- MODERATION COMMANDS (short versions) ---
@bot.tree.command(name="ban", description="🔨 Ban a user")
@app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="User to ban", reason="Reason")
async def ban_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "ban", reason)
    await interaction.response.send_message(f"⚠️ Ban {user.mention}?", view=view, ephemeral=True)

@bot.tree.command(name="kick", description="👢 Kick a user")
@app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="User to kick", reason="Reason")
async def kick_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "kick", reason)
    await interaction.response.send_message(f"⚠️ Kick {user.mention}?", view=view, ephemeral=True)

@bot.tree.command(name="timeout", description="⏰ Timeout a user")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User", minutes="Minutes", reason="Reason")
async def timeout_cmd(interaction: discord.Interaction, user: discord.Member, minutes: int = 60, reason: str = "No reason"):
    await interaction.response.defer(ephemeral=True)
    await user.timeout(timedelta(minutes=minutes), reason=f"Kers0ne: {reason}")
    await log_action(interaction.guild, "⏰ TIMEOUT", user, f"{minutes}min, Reason: {reason}")
    await interaction.followup.send(f"✅ {user} timed out for {minutes} minutes", ephemeral=True)

@bot.tree.command(name="untimeout", description="⏰ Remove timeout")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User to untimeout")
async def untimeout_cmd(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    await user.timeout(None)
    await log_action(interaction.guild, "⏰ TIMEOUT REMOVED", user, "Timeout removed")
    await interaction.followup.send(f"✅ {user} untimed out", ephemeral=True)

@bot.tree.command(name="mute", description="🔇 Mute a user")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="User to mute", reason="Reason")
async def mute_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "mute", reason)
    await interaction.response.send_message(f"⚠️ Mute {user.mention}?", view=view, ephemeral=True)

@bot.tree.command(name="unmute", description="🔊 Unmute a user")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="User to unmute")
async def unmute_cmd(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if mute_role:
        await user.remove_roles(mute_role)
        await log_action(interaction.guild, "🔊 UNMUTED", user, "Unmuted")
        await interaction.followup.send(f"✅ {user} unmuted", ephemeral=True)
    else:
        await interaction.followup.send("❌ Muted role not found", ephemeral=True)

@bot.tree.command(name="punish", description="🛡️ Choose punishment")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User to punish", reason="Reason")
async def punish_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = PunishmentSelect(user, interaction.guild, reason)
    await interaction.response.send_message(f"🛡️ Punish {user.mention}", view=view, ephemeral=True)

@bot.tree.command(name="removeroles", description="⚔️ Remove all roles")
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(user="User to strip", reason="Reason")
async def removeroles_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    view = ConfirmView(user, interaction.guild, "remove_roles", reason)
    await interaction.response.send_message(f"⚠️ Remove roles from {user.mention}?", view=view, ephemeral=True)

@bot.tree.command(name="nick", description="✏️ Change nickname")
@app_commands.default_permissions(manage_nicknames=True)
@app_commands.describe(user="User", nickname="New nickname")
async def nick_cmd(interaction: discord.Interaction, user: discord.Member, nickname: str = None):
    old = user.display_name
    await user.edit(nick=nickname)
    await log_action(interaction.guild, "✏️ NICKNAME CHANGED", interaction.user, f"User: {user}\nOld: {old}\nNew: {nickname or 'Reset'}")
    await interaction.response.send_message(f"✅ Changed nickname for {user.mention}", ephemeral=True)

@bot.tree.command(name="slowmode", description="⏱️ Set slowmode")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(seconds="Seconds", channel="Channel")
async def slowmode_cmd(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
    target = channel or interaction.channel
    await target.edit(slowmode_delay=seconds)
    await log_action(interaction.guild, "⏱️ SLOWMODE SET", interaction.user, f"Channel: #{target.name}\nSeconds: {seconds}")
    await interaction.response.send_message(f"✅ Slowmode set to {seconds}s in #{target.name}", ephemeral=True)

# --- LOCK COMMANDS ---
@bot.tree.command(name="lock", description="🔒 Lock a channel")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(channel="Channel", reason="Reason")
async def lock_cmd(interaction: discord.Interaction, channel: discord.TextChannel, reason: str = "No reason"):
    await interaction.response.defer(ephemeral=True)
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await log_action(interaction.guild, "🔒 CHANNEL LOCKED", interaction.user, f"Channel: #{channel.name}\nReason: {reason}")
    await interaction.followup.send(f"🔒 #{channel.name} locked", ephemeral=True)

@bot.tree.command(name="unlock", description="🔓 Unlock a channel")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(channel="Channel")
async def unlock_cmd(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    await channel.set_permissions(interaction.guild.default_role, send_messages=None)
    await log_action(interaction.guild, "🔓 CHANNEL UNLOCKED", interaction.user, f"Channel: #{channel.name}")
    await interaction.followup.send(f"🔓 #{channel.name} unlocked", ephemeral=True)

@bot.tree.command(name="lockall", description="🔒 Lock ALL channels")
@app_commands.default_permissions(administrator=True)
async def lockall_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for ch in interaction.guild.channels:
        try:
            if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                await ch.set_permissions(interaction.guild.default_role, send_messages=False, connect=False, speak=False)
                count += 1
                await asyncio.sleep(0.2)
        except:
            pass
    await log_action(interaction.guild, "🔒 LOCKALL", interaction.user, f"Locked {count} channels")
    await interaction.followup.send(f"🔒 Locked {count} channels", ephemeral=True)

@bot.tree.command(name="unlockall", description="🔓 Unlock ALL channels")
@app_commands.default_permissions(administrator=True)
async def unlockall_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for ch in interaction.guild.channels:
        try:
            if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                await ch.set_permissions(interaction.guild.default_role, send_messages=None, connect=None, speak=None)
                count += 1
                await asyncio.sleep(0.2)
        except:
            pass
    await log_action(interaction.guild, "🔓 UNLOCKALL", interaction.user, f"Unlocked {count} channels")
    await interaction.followup.send(f"🔓 Unlocked {count} channels", ephemeral=True)

# --- CLEANUP COMMANDS ---
@bot.tree.command(name="purge", description="🧹 Delete messages")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount="Number of messages", user="Filter by user")
async def purge_cmd(interaction: discord.Interaction, amount: int, user: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    def check(m): return m.author == user if user else True
    deleted = await interaction.channel.purge(limit=amount, check=check)
    await log_action(interaction.guild, "🧹 PURGE", interaction.user, f"Deleted {len(deleted)} messages")
    await interaction.followup.send(f"✅ Deleted {len(deleted)} messages", ephemeral=True)

@bot.tree.command(name="clear", description="🧹 DELETE ALL messages")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel")
async def clear_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target = channel or interaction.channel
    view = ClearConfirmView(target, interaction.guild, interaction.user)
    await interaction.response.send_message(f"⚠️ Delete ALL in #{target.name}?", view=view, ephemeral=True)

@bot.tree.command(name="deletetext", description="🗑️ Delete text only")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel", limit="Max messages")
async def deletetext_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None, limit: int = 1000):
    target = channel or interaction.channel
    view = DeleteTextConfirmView(target, interaction.guild, interaction.user, limit)
    await interaction.response.send_message(f"⚠️ Delete text in #{target.name}?", view=view, ephemeral=True)

@bot.tree.command(name="deletefiles", description="🗑️ Delete files only")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(channel="Channel", limit="Max messages")
async def deletefiles_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None, limit: int = 1000):
    target = channel or interaction.channel
    view = DeleteFilesConfirmView(target, interaction.guild, interaction.user, limit)
    await interaction.response.send_message(f"⚠️ Delete files in #{target.name}?", view=view, ephemeral=True)

# --- SERVER CONTROL ---
@bot.tree.command(name="lockdown", description="🔒 Lock down server")
@app_commands.default_permissions(administrator=True)
async def lockdown_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    for ch in interaction.guild.channels:
        if isinstance(ch, discord.TextChannel):
            await ch.set_permissions(interaction.guild.default_role, send_messages=False)
    await log_action(interaction.guild, "🔒 LOCKDOWN", interaction.user, "Server locked")
    await interaction.followup.send("🔒 Server locked", ephemeral=True)

@bot.tree.command(name="unlockserver", description="🔓 Unlock server")
@app_commands.default_permissions(administrator=True)
async def unlockserver_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    for ch in interaction.guild.channels:
        if isinstance(ch, discord.TextChannel):
            await ch.set_permissions(interaction.guild.default_role, send_messages=None)
    await log_action(interaction.guild, "🔓 UNLOCKED", interaction.user, "Server unlocked")
    await interaction.followup.send("🔓 Server unlocked", ephemeral=True)

@bot.tree.command(name="deleteallchannels", description="💀 DELETE ALL channels")
@app_commands.default_permissions(administrator=True)
async def deleteall_cmd(interaction: discord.Interaction):
    view = DeleteAllConfirmView(interaction.guild, interaction.user)
    await interaction.response.send_message("💀 Delete ALL channels?", view=view, ephemeral=True)

# --- TICKET COMMANDS ---
@bot.tree.command(name="ticket", description="🎫 Create a ticket")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(reason="Reason")
async def ticket_cmd(interaction: discord.Interaction, reason: str = "Support request"):
    guild = interaction.guild
    ticket_category = discord.utils.get(guild.categories, name="TICKETS")
    if not ticket_category:
        ticket_category = await guild.create_category("TICKETS")
    ticket_name = f"ticket-{interaction.user.name.lower()}"
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)}
    admin_role = discord.utils.get(guild.roles, name="Admin")
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    ticket_channel = await ticket_category.create_text_channel(ticket_name, overwrites=overwrites)
    embed = Embed(title="🎫 Ticket Created", description=f"**User:** {interaction.user.mention}\n**Reason:** {reason}", color=Color.dark_gray())
    await ticket_channel.send(embed=embed)
    await log_action(guild, "🎫 TICKET CREATED", interaction.user, f"Reason: {reason}")
    await interaction.response.send_message(f"✅ Ticket created! Check #{ticket_channel.name}", ephemeral=True)

@bot.tree.command(name="ticketsetup", description="🎫 Setup ticket system")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(channel="Channel for ticket panel")
async def ticketsetup_cmd(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = Embed(title="🎫 Ticket System", description="Click below to create a ticket.", color=Color.dark_gray())
    await channel.send(embed=embed, view=TicketButtonView())
    await interaction.response.send_message(f"✅ Ticket panel sent to #{channel.name}", ephemeral=True)

@bot.tree.command(name="closeticket", description="🔒 Close ticket")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(reason="Reason")
async def closeticket_cmd(interaction: discord.Interaction, reason: str = "No reason"):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Not a ticket channel.", ephemeral=True)
        return
    await log_action(interaction.guild, "🔒 TICKET CLOSED", interaction.user, f"Reason: {reason}")
    await interaction.response.send_message(f"🔒 Ticket closed. Reason: {reason}", ephemeral=True)
    await interaction.channel.send(f"🔒 Ticket closed by {interaction.user.mention}")
    await asyncio.sleep(2)
    await interaction.channel.delete()

# --- EMBED COMMANDS ---
@bot.tree.command(name="create-embed", description="📝 Create custom embed")
@app_commands.default_permissions(administrator=True)
async def create_embed_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedModal())

@bot.tree.command(name="embed", description="📝 Send embed to channel")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(channel="Channel", title="Title", description="Description", color="Hex color", footer="Footer")
async def embed_cmd(interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str, color: str = None, footer: str = None):
    embed = Embed(title=title, description=description, color=Color.dark_gray())
    if color:
        try:
            embed.color = Color(int(color.replace("#", ""), 16))
        except:
            pass
    if footer:
        embed.set_footer(text=footer)
    embed.timestamp = datetime.utcnow()
    await channel.send(embed=embed)
    await log_action(interaction.guild, "📝 EMBED SENT", interaction.user, f"Channel: #{channel.name}\nTitle: {title}")
    await interaction.response.send_message(f"✅ Embed sent to #{channel.name}", ephemeral=True)

# --- UTILITY COMMANDS ---
@bot.tree.command(name="announce", description="📢 Send announcement")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(channel="Channel", title="Title", message="Message")
async def announce_cmd(interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
    embed = Embed(title=title, description=message, color=Color.dark_gray(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"Announcement by {interaction.user}")
    await channel.send(embed=embed)
    await log_action(interaction.guild, "📢 ANNOUNCEMENT", interaction.user, f"Channel: #{channel.name}\nTitle: {title}")
    await interaction.response.send_message(f"✅ Announcement sent to #{channel.name}", ephemeral=True)

@bot.tree.command(name="poll", description="📊 Create poll")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(channel="Channel", question="Question", option1="Option 1", option2="Option 2", option3="Option 3", option4="Option 4")
async def poll_cmd(interaction: discord.Interaction, channel: discord.TextChannel, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    options = [option1, option2] + ([option3] if option3 else []) + ([option4] if option4 else [])
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    poll_text = f"**{question}**\n\n" + "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
    embed = Embed(title="📊 Poll", description=poll_text, color=Color.dark_gray())
    poll_msg = await channel.send(embed=embed)
    for i in range(len(options)):
        await poll_msg.add_reaction(emojis[i])
    await log_action(interaction.guild, "📊 POLL CREATED", interaction.user, f"Question: {question}")
    await interaction.response.send_message(f"✅ Poll created in #{channel.name}", ephemeral=True)

@bot.tree.command(name="setup", description="🔧 Setup logs channel")
@app_commands.default_permissions(administrator=True)
async def setup_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await setup_logs_channel(interaction.guild)
    await interaction.followup.send("✅ Logs channel created", ephemeral=True)

@bot.tree.command(name="stats", description="📊 Server stats")
@app_commands.default_permissions(administrator=True)
async def stats_cmd(interaction: discord.Interaction):
    guild = interaction.guild
    embed = Embed(title=f"📊 Server Stats - {guild.name}", color=Color.dark_gray())
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="say", description="💬 Make bot say")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(message="Message", channel="Channel")
async def say_cmd(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    target = channel or interaction.channel
    await target.send(message)
    await interaction.response.send_message(f"✅ Message sent to #{target.name}", ephemeral=True)

@bot.tree.command(name="dm", description="📩 DM a user")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="User", message="Message")
async def dm_cmd(interaction: discord.Interaction, user: discord.Member, message: str):
    try:
        await user.send(message)
        await log_action(interaction.guild, "📩 DM SENT", interaction.user, f"To: {user}\nMessage: {message[:50]}...")
        await interaction.response.send_message(f"✅ DM sent to {user.mention}", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Failed to DM user.", ephemeral=True)

# --- WARN COMMANDS ---
@bot.tree.command(name="warn", description="⚠️ Warn a user")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User", reason="Reason")
async def warn_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    if interaction.guild.id not in warnings_db:
        warnings_db[interaction.guild.id] = {}
    if user.id not in warnings_db[interaction.guild.id]:
        warnings_db[interaction.guild.id][user.id] = []
    warnings_db[interaction.guild.id][user.id].append({"reason": reason, "moderator": interaction.user.id, "timestamp": datetime.utcnow().isoformat()})
    await log_action(interaction.guild, "⚠️ USER WARNED", user, f"Reason: {reason}\nModerator: {interaction.user}")
    await interaction.response.send_message(f"⚠️ {user.mention} warned. Reason: {reason}", ephemeral=True)

@bot.tree.command(name="warnings", description="📋 View warnings")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User")
async def warnings_cmd(interaction: discord.Interaction, user: discord.Member):
    guild_warnings = warnings_db.get(interaction.guild.id, {})
    user_warnings = guild_warnings.get(user.id, [])
    if not user_warnings:
        await interaction.response.send_message(f"✅ {user.mention} has no warnings.", ephemeral=True)
        return
    embed = Embed(title=f"⚠️ Warnings for {user}", color=Color.dark_gray())
    for i, warn in enumerate(user_warnings, 1):
        mod = interaction.guild.get_member(warn['moderator'])
        mod_name = mod.mention if mod else "Unknown"
        embed.add_field(name=f"Warning #{i}", value=f"Reason: {warn['reason']}\nModerator: {mod_name}\nTime: {warn['timestamp'][:16]}", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="clearwarnings", description="🗑️ Clear warnings")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User")
async def clearwarnings_cmd(interaction: discord.Interaction, user: discord.Member):
    if interaction.guild.id in warnings_db and user.id in warnings_db[interaction.guild.id]:
        del warnings_db[interaction.guild.id][user.id]
        await log_action(interaction.guild, "🗑️ WARNINGS CLEARED", user, f"By: {interaction.user}")
        await interaction.response.send_message(f"✅ Cleared warnings for {user.mention}", ephemeral=True)
    else:
        await interaction.response.send_message(f"✅ {user.mention} has no warnings.", ephemeral=True)

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
# AUTO-PROTECTION EVENTS
# ============================================================
@bot.event
async def on_ready():
    print(f"✅ Kers0ne Bot online — {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"⚠️ Could not sync commands: {e}")

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
        new = await guild.create_text_channel("💀-kers0ne-strikes-back")
        await new.send("**ALL CHANNELS OBLITERATED.** You nuked Kers0ne.")
    except:
        pass

# ============================================================
# MAIN — RUN BOTH WEB SERVER AND DISCORD BOT
# ============================================================
if __name__ == "__main__":
    # Start web server in background thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Web server started on port " + os.environ.get("PORT", "5000"))
    
    # Run Discord bot
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
