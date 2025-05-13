import discord
import asyncio
import time
import os
import random
from datetime import datetime
import requests
from colorama import Fore, Style, init
import logging
import sys

# Initialize colorama and disable all logging
init()
logger = logging.getLogger('discord')
logger.setLevel(logging.CRITICAL)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(''))
logger.addHandler(handler)

def animate_text(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_banner():
    banner = f"""
{Fore.YELLOW}
 ██████╗ ██╗    ██╗ ██████╗ 
██╔═══██╗██║    ██║██╔═══██╗
██║   ██║██║ █╗ ██║██║   ██║
██║   ██║██║███╗██║██║   ██║
╚██████╔╝╚███╔███╔╝╚██████╔╝
 ╚═════╝  ╚══╝╚══╝  ╚═════╝ 
{Fore.RED}
██╗  ██╗ █████╗ ██████╗██╗  ██╗
██║  ██║██╔══██╗██╔════╝██║ ██╔╝
███████║███████║██║     █████╔╝ 
██╔══██║██╔══██║██║     ██╔═██╗ 
██║  ██║██║  ██║╚██████╗██║  ██╗
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
{Style.RESET_ALL}
{Fore.CYAN}• ᴄʀᴇᴀᴛᴇᴅ ʙʏ ᴀᴅɪᴛʏᴀ •{Style.RESET_ALL}
{Fore.MAGENTA}• ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕʏѕᴛᴇᴍ •{Style.RESET_ALL}
"""
    print(banner)

def get_config():
    config_path = "config.txt"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            lines = f.readlines()
            if len(lines) >= 3:
                return {
                    "token": lines[0].strip(),
                    "owner_id": int(lines[1].strip()),
                    "channel_id": int(lines[2].strip())
                }
    
    # If config doesn't exist or is incomplete, ask for new values
    print(f"{Fore.YELLOW}⮞ {Fore.WHITE}First time setup required")
    token = input(f"{Fore.YELLOW}⮞ {Fore.WHITE}Enter Bot Token: ").strip()
    owner_id = input(f"{Fore.YELLOW}⮞ {Fore.WHITE}Enter Owner ID: ").strip()
    channel_id = input(f"{Fore.YELLOW}⮞ {Fore.WHITE}Enter Channel ID: ").strip()
    
    # Validate inputs
    try:
        owner_id = int(owner_id)
        channel_id = int(channel_id)
    except ValueError:
        print(f"{Fore.RED}Error: Owner ID and Channel ID must be numbers")
        exit()
    
    # Save to file
    with open(config_path, "w") as f:
        f.write(f"{token}\n{owner_id}\n{channel_id}")
    
    return {
        "token": token,
        "owner_id": owner_id,
        "channel_id": channel_id
    }

# Get configuration
config = get_config()
TOKEN = config["token"]
OWNER_ID = config["owner_id"]
CHANNEL_ID = config["channel_id"]

class OwoBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True
        self.first_stats_display = True
        self.commands = {
            "hunt": {"active": True, "count": 0, "cooldown": (11, 13)},
            "battle": {"active": True, "count": 0, "cooldown": (11, 13)},
            "pray": {"active": True, "count": 0, "last_used": 0, "cooldown": random.randint(300, 360)},
            "cf": {"active": False, "count": 0, "cooldown": (11, 13)}
        }
        self.start_time = datetime.now()
        self.channel_id = CHANNEL_ID
        self.owner_id = OWNER_ID
        self.webhook_url = "https://discord.com/api/webhooks/1368997335614623767/-MMVR6HAAYsSfIkh-gX1467EuWMQAqw_QzhRlRkl5CJssifAKYoMzDP27CRDedj3Uail"
        self.suspicious_words = [
            "captcha", "verify", "warning", "human6", 
            "human", "real human", "⚠️", "please complete"
        ]
        self.random_texts = [
            "lol", "nice", "gg", "wow", "omg", 
            "xd", "lmao", "cool", "awesome", "sick",
            "pog", "poggers", "lets go", "yay", "no way",
            "that's crazy", "insane", "wild", "unreal", "sheesh",
            "fr?", "dead", "rip", "f", "big oof",
            "oof", "ouch", "yikes", "bruh", "cap"
        ]
        self.spam_task = None
        self.stats_task = None
        self.random_text_task = None
        self.last_update = datetime.now()
        self.captcha_count = 0
        print_banner()

    async def vibrate_device(self, times=100, duration=1000):
        """Vibrate the device multiple times"""
        if os.name == 'posix':  # Android (Termux)
            for _ in range(times):
                os.system(f'termux-vibrate -d {duration} &')
                await asyncio.sleep(0.5)  # Short pause between vibrations
            os.system('termux-toast -b red -c white "⚠️ CAPTCHA DETECTED!" &')

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def generate_stats_text(self):
        total = sum(cmd["count"] for cmd in self.commands.values())
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        now = datetime.now()
        time_since_last = now - self.last_update
        self.last_update = now
        
        # Calculate pray cooldown (5-6 minutes)
        time_since_pray = time.time() - self.commands['pray']['last_used']
        pray_cooldown = max(0, self.commands['pray']['cooldown'] - time_since_pray)
        pray_min = int(pray_cooldown // 60)
        pray_sec = int(pray_cooldown % 60)
        
        # Calculate commands per hour
        uptime_hours = max(1, uptime.total_seconds() / 3600)
        cph = int(total / uptime_hours)
        
        return f"""
{Fore.YELLOW}⚡ {Fore.RED}LIVE GRINDING STATS {Fore.YELLOW}⚡{Fore.CYAN}
╔════════════════════════════════╗
║ {Fore.GREEN}🦊 ᴏᴡᴏ ʜᴜɴᴛ:    {self.commands['hunt']['count']:>3} {Fore.CYAN}║          ║
║ {Fore.RED}⚔️ ᴏᴡᴏ ʙᴀᴛᴛʟᴇ:   {self.commands['battle']['count']:>3} {Fore.CYAN}║          ║
║ {Fore.BLUE}🙏 ᴏᴡᴏ ᴘʀᴀʏ:    {self.commands['pray']['count']:>3} {Fore.CYAN}║          ║
║ {Fore.YELLOW}🎲 ᴏᴡᴏ ᴄꜰ:      {self.commands['cf']['count']:>3} {Fore.CYAN}║          ║
╠════════════════════════════════╣
║ {Fore.YELLOW}📊 Total:    {total:>8} {Fore.CYAN}║        ║
║ {Fore.CYAN}⏱️ Uptime:  {hours:02d}h {minutes:02d}m {seconds:02d}s║        ║
║ {Fore.CYAN}🚀 Cmd/Hour: {cph:>8} {Fore.CYAN}║        ║
╠════════════════════════════════╣
{Style.RESET_ALL}

{Fore.YELLOW}🔹 {Fore.RED}Current Status: {'RUNNING' if self.running else 'STOPPED'}
{Fore.YELLOW}🔹 {Fore.RED}ɴᴇхᴛ ᴘʀᴀʏ: {pray_min:02d}m {pray_sec:02d}s

{Fore.RED}╔══════════════════════════╗
{Fore.RED}║ 🚨 ᴄᴀᴘᴛᴄʜᴀ: {self.captcha_count:>10} ║
{Fore.RED}╚══════════════════════════╝
{Style.RESET_ALL}
"""

    async def show_stats(self):
        while True:
            self.clear_terminal()
            print_banner()
            
            stats_text = self.generate_stats_text()
            
            if self.first_stats_display:
                animate_text(stats_text)
                self.first_stats_display = False
            else:
                print(stats_text)
            
            await asyncio.sleep(2)

    async def on_ready(self):
        animate_text(f"\n{Fore.GREEN}✅ Successfully connected to Discord API")
        animate_text(f"{Fore.YELLOW}⚡ Initializing Owo grinding systems...")
        await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="🚀 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ"))
        if self.running:
            self.spam_task = asyncio.create_task(self.spam_commands())
            self.stats_task = asyncio.create_task(self.show_stats())
            self.random_text_task = asyncio.create_task(self.send_random_text())
            animate_text(f"{Fore.GREEN}🚀 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ{Style.RESET_ALL}")

    async def send_random_text(self):
        channel = self.get_channel(self.channel_id)
        while self.running:
            try:
                # Random delay between 1-5 minutes
                await asyncio.sleep(random.randint(60, 300))
                
                # Random chance to send text (60% chance)
                if random.random() < 0.6:
                    # Select random text and possibly add emojis
                    text = random.choice(self.random_texts)
                    if random.random() < 0.4:  # 40% chance to add emoji
                        emojis = ["😂", "😆", "😅", "🤣", "🙄", "😳", "🥲", "😭", "💀", "🔥"]
                        text += " " + random.choice(emojis)
                    
                    # Sometimes add multiple texts
                    if random.random() < 0.2:  # 20% chance for multi-text
                        text += " " + random.choice(self.random_texts)
                    
                    await channel.send(text)
                    
                    # Small chance to send follow-up message
                    if random.random() < 0.1:  # 10% chance
                        await asyncio.sleep(random.randint(2, 5))
                        await channel.send(random.choice(["lol", "xd", "fr", "no way"]))
            
            except Exception as e:
                print(f"{Fore.RED}Error in random text: {e}{Style.RESET_ALL}")
                await asyncio.sleep(30)

    async def send_webhook_alert(self, message):
        current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = {
            "title": "<a:Danger:1369049718465892405> ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ <a:danger:1369049678821458022>",
            "description": (
                f"**<a:hacker:1369053268394770524> ᴏᴡᴏ ѕᴄʀɪᴘᴛ ᴏᴡɴᴇʀ:** <@{self.owner_id}>\n"
                f"**<a:Danger:1369049718465892405> ᴄᴀᴘᴛᴄʜᴀ sᴇɴᴅᴇʀ:** {message.author.mention}\n"
                f"**<:channels:1369052812981309482> ᴄʜᴀɴɴᴇʟ:** {message.channel.mention}\n\n"
                f"**<a:earth:1369054330367512757> ʟᴀѕᴛ ᴛɪᴍᴇ ѕᴛᴀᴛѕ**\n"
                f"<:Diamond:1369050560673878060> ᴏᴡᴏ ʜᴜɴᴛ: `{self.commands['hunt']['count']}`\n"
                f"<a:redeye:1369051355112673320> ᴏᴡᴏ ʙᴀᴛᴛʟᴇ: `{self.commands['battle']['count']}`\n"
                f"<a:prays:1369051991468277871> ᴏᴡᴏ ᴘʀᴀʏ: `{self.commands['pray']['count']}`\n"
                f"<a:time:1369052336239935509> ᴜᴘᴛɪᴍᴇ: `{hours}h {minutes}m {seconds}s`\n\n"
                f"**ᴠᴇʀɪғʏ ʟɪɴᴋ:** [ᴄʟɪᴄᴋ ʜᴇʀᴇ](https://owobot.com/captcha)\n\n"
                f"**ᴍᴇѕѕᴀɢᴇ ᴅᴇᴛᴇᴄᴛᴇᴅ:**\n```\n{message.content}\n```"
            ),
            "color": 16711680,
            "footer": {
                "text": f"ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴀʟᴇʀᴛ • {current_time}",
                "icon_url": "https://cdn.discordapp.com/emojis/1235116899306835968.gif"
            }
        }
        
        avatar = str(self.user.avatar.url) if self.user.avatar else "https://cdn.discordapp.com/emojis/988221156389572658.webp"
        requests.post(self.webhook_url, json={
            "content": f"<@{self.owner_id}>",
            "embeds": [embed],
            "username": "ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴀʟᴇʀᴛ",
            "avatar_url": avatar
        })

    async def handle_captcha(self, message):
        # Immediately stop all commands
        self.running = False
        self.captcha_count += 1
        
        # Record stats before stopping
        stats_text = self.generate_stats_text()
        self.clear_terminal()
        print_banner()
        print(stats_text)
        
        # Send webhook and vibrate (in background)
        asyncio.create_task(self.send_webhook_alert(message))
        asyncio.create_task(self.vibrate_device())
        
        # Change presence and notify
        await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="🚨 ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ ⚠️"))
        animate_text(f"\n{Fore.RED}🚨 ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ ⚠️")
        
        # Cancel tasks
        if self.spam_task:
            self.spam_task.cancel()
        if self.stats_task:
            self.stats_task.cancel()
        if self.random_text_task:
            self.random_text_task.cancel()

    async def stop_bot(self):
        self.running = False
        if self.spam_task:
            self.spam_task.cancel()
        if self.stats_task:
            self.stats_task.cancel()
        if self.random_text_task:
            self.random_text_task.cancel()
        animate_text(f"\n{Fore.RED}⚠️ ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ 🚨")
        await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="⚠️ ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ 🚨"))

    async def on_message(self, message):
        if message.channel.id == self.channel_id and any(word in message.content.lower() for word in self.suspicious_words):
            if not ("owo battle" in message.content.lower() and "⚠️" in message.content):
                if self.running:
                    await self.handle_captcha(message)
                return

        if message.author.id != self.user.id:
            # Only allow owner to use commands
            if message.author.id != self.owner_id:
                return

            if message.content.lower().startswith("!owo set channel"):
                try:
                    channel_id = int(message.content.split()[-1])
                    self.channel_id = channel_id
                    await message.channel.send(f"✅ Channel set to {channel_id} (This setting is temporary and won't be saved)")
                    return
                except (ValueError, IndexError):
                    await message.channel.send("❌ Invalid channel ID format. Use `!owo set channel <channel_id>`")
                    return

            if message.content.lower().startswith("!owohunt "):
                state = message.content.lower().split()[1]
                if state == "on":
                    self.commands["hunt"]["active"] = True
                    await message.channel.send("✅ OwO Hunt commands enabled")
                elif state == "off":
                    self.commands["hunt"]["active"] = False
                    await message.channel.send("❌ OwO Hunt commands disabled")
                return

            if message.content.lower().startswith("!owobattle "):
                state = message.content.lower().split()[1]
                if state == "on":
                    self.commands["battle"]["active"] = True
                    await message.channel.send("✅ OwO Battle commands enabled")
                elif state == "off":
                    self.commands["battle"]["active"] = False
                    await message.channel.send("❌ OwO Battle commands disabled")
                return

            if message.content.lower().startswith("!owopray "):
                state = message.content.lower().split()[1]
                if state == "on":
                    self.commands["pray"]["active"] = True
                    await message.channel.send("✅ ``ᴏᴡᴏ ᴘʀᴀʏ ᴄᴍᴅ ɪѕ ᴇɴᴀʙʟᴇᴅ``")
                elif state == "off":
                    self.commands["pray"]["active"] = False
                    await message.channel.send("❌ ``ᴏᴡᴏ ᴘʀᴀʏ ᴄᴍᴅ ɪѕ ᴅɪѕᴀʙʟᴇᴅ``")
                return

            if message.content.lower().startswith("!owocf "):
                state = message.content.lower().split()[1]
                if state == "on":
                    self.commands["cf"]["active"] = True
                    await message.channel.send("✅ ``ᴏᴡᴏ ᴄꜰ ᴄᴍᴅ ɪѕ ᴇɴᴀʙʟᴇᴅ``")
                elif state == "off":
                    self.commands["cf"]["active"] = False
                    await message.channel.send("❌ ``ᴏᴡᴏ ᴄꜰ ᴄᴍᴅ ɪѕ ᴅɪѕᴀʙʟᴇᴅ``")
                return

            if message.content.lower() == "stats":
                uptime = datetime.now() - self.start_time
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                total_cmds = sum(cmd["count"] for cmd in self.commands.values())

                stats_msg = (
                    f"```ansi\n\u001b[36m"
                    f"📊 Owo Bot Stats\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🦊 Hunts   : {self.commands['hunt']['count']}\n"
                    f"⚔️ Battles : {self.commands['battle']['count']}\n"
                    f"🙏 Prays   : {self.commands['pray']['count']}\n"
                    f"🎲 CFs     : {self.commands['cf']['count']}\n"
                    f"📊 Total   : {total_cmds}\n"
                    f"🕒 Uptime  : {hours}h {minutes}m {seconds}s\n"
                    f"🚨 Captchas: {self.captcha_count}\n"
                    f"📅 Started : {self.start_time.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"\u001b[0m```"
                )
                await message.channel.send(stats_msg)
                return

            if message.content.lower() == "!owocmdstats":
                stats = (
                    f"```\n"
                    f"OwO Command Status:\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"Hunt   : {'✅ ON' if self.commands['hunt']['active'] else '❌ OFF'}      ʟᴏᴡ ʀɪѕᴋ\n"
                    f"Battle : {'✅ ON' if self.commands['battle']['active'] else '❌ OFF'}    ʟᴏᴡ ʀɪѕᴋ\n"
                    f"Pray   : {'✅ ON' if self.commands['pray']['active'] else '❌ OFF'}      ᴍᴇᴅɪᴜᴍ ʀɪѕᴋ\n"
                    f"CF     : {'✅ ON' if self.commands['cf']['active'] else '❌ OFF'}     ʜɪɢʜ ʀɪѕᴋ\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"```"
                )
                await message.channel.send(stats)
                return

            if message.content.lower() == "!start":
                if not self.running:
                    self.running = True
                    self.start_time = datetime.now()
                    self.spam_task = asyncio.create_task(self.spam_commands())
                    self.stats_task = asyncio.create_task(self.show_stats())
                    self.random_text_task = asyncio.create_task(self.send_random_text())
                    await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="🚀 ᴏᴡᴏ ʜᴀᴄᴋ ᴍᴏᴅᴇ"))
                    await message.channel.send("✅ ᴏᴡᴏ ʜᴀᴄᴋᴇʀ ᴍᴏᴅᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ")
                    animate_text(f"\n{Fore.GREEN}⚡ Owo Hacker Mode restarted!")
                else:
                    await message.channel.send("ℹ️ ᴏᴡᴏ ʜᴀᴄᴋᴇʀ ᴍᴏᴅᴇ ɪꜱ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ!")
                return

            if message.content.lower() == "!stop":
                if self.running:
                    await self.stop_bot()
                    await message.channel.send("🛑 ᴏᴡᴏ ʜᴀᴄᴋᴇʀ ᴍᴏᴅᴇ ᴅᴇᴀᴄᴛɪᴠᴀᴛᴇᴅ")
                else:
                    await message.channel.send("ℹ️ ᴏᴡᴏ ʜᴀᴄᴋᴇʀ ᴍᴏᴅᴇ ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴛᴏᴘᴘᴇᴅ!")
                return

        if message.content.lower() == "owo inv":
            return

    async def spam_commands(self):
        channel = self.get_channel(self.channel_id)
        while self.running:
            try:
                if self.commands["hunt"]["active"]:
                    await channel.send("owo hunt")
                    self.commands["hunt"]["count"] += 1
                    await asyncio.sleep(random.randint(11, 13))

                if self.commands["battle"]["active"]:
                    await channel.send("owo battle")
                    self.commands["battle"]["count"] += 1
                    await asyncio.sleep(random.randint(11, 13))

                if (self.commands["pray"]["active"] and
                    time.time() - self.commands["pray"]["last_used"] >= self.commands["pray"]["cooldown"]):
                    await channel.send("owo pray")
                    self.commands["pray"]["count"] += 1
                    self.commands["pray"]["last_used"] = time.time()
                    # Randomize next pray cooldown between 5-6 minutes (300-360 seconds)
                    self.commands["pray"]["cooldown"] = random.randint(300, 360)
                    await asyncio.sleep(random.randint(5, 8))

                if self.commands["cf"]["active"]:
                    await channel.send("owo cf 1")
                    self.commands["cf"]["count"] += 1
                    await asyncio.sleep(random.randint(11, 13))

            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                await asyncio.sleep(5)

# Run the bot
client = OwoBot()
client.run(TOKEN, log_handler=None)
