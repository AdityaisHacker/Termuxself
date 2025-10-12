import discord
import asyncio
import time
import os
import random
from datetime import datetime, timedelta
import requests
from colorama import Fore, Style, init
import logging
import sys

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
██╗░░██╗░█████╗░░█████╗░██╗░░██╗
██╗░░██║██╔══██╗██╔══██╗██║░██╔╝
███████║███████║██║░░╚═╝█████═╝░
██╔══██║██╔══██║██║░░██╗██╔═██╗░
██║░░██║██║░░██║╚█████╔╝██║░╚██╗
╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝

{Style.RESET_ALL}
{Fore.CYAN}• ᴄʀᴇᴀᴛᴇᴅ ʙʏ ᴀᴅɪᴛʏᴀ  •{Style.RESET_ALL}
{Fore.MAGENTA}• ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕʏѕᴛᴇᴍ •{Style.RESET_ALL}
"""
    print(banner)

def get_token():
    token_path = "token.txt"
    if os.path.exists(token_path):
        with open(token_path, "r") as f:
            return f.read().strip()
    new_token = input(f"{Fore.YELLOW}⮞ {Fore.WHITE}Enter Token: ").strip()
    with open(token_path, "w") as f:
        f.write(new_token)
    return new_token

TOKEN = get_token()

class OwoBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True
        self.first_stats_display = True
        self.commands = {
            "hunt": {"active": True, "count": 0, "cooldown": (11, 13)},
            "battle": {"active": True, "count": 0, "cooldown": (11, 13)},
            "pray": {"active": True, "count": 0, "last_used": 0, "cooldown": random.randint(300, 360)},
            "owo": {"active": False, "count": 0, "cooldown": (11, 13)},
            "daily": {"active": False, "count": 0, "last_used": 0, "cooldown": 86400}
        }
        self.start_time = datetime.now()
        self.channel_id = 1359628652924371270
        self.webhook_url = "https://discord.com/api/webhooks/1368997335614623767/-MMVR6HAAYsSfIkh-gX1467EuWMQAqw_QzhRlRkl5CJssifAKYoMzDP27CRDedj3Uail"
        self.suspicious_words = [
            "captcha", "verify", "warning", "human6", 
            "human", "real human", "⚠️", "please complete"
        ]
        self.spam_task = None
        self.stats_task = None
        self.time_check_task = None
        self.last_update = datetime.now()
        self.captcha_detected = False
        self.daily_claimed = False
        
        self.scheduled_stop_time = None
        self.auto_stop_enabled = False
        
        self.random_texts = [
            "lol", "nice", "gg", "wow", "cool", "awesome", 
            "let's go", "yay", "lmao", "haha", "xd", 
            "good game", "nice one", "wowzers", "omg",
            "that's crazy", "insane", "unbelievable", "pog",
            "poggers", "let's get it", "grinding time"
        ]
        self.random_emojis = [
            "😂", "😊", "👍", "✨", "❤️", "🔥", "🎉", "🤣", 
            "😎", "👀", "💯", "🙌", "😍", "🥳", "😆", "🤩",
            "😅", "🤔", "😁", "👏", "🤪", "😜", "🤗", "😇"
        ]
        self.random_actions = [
            "owo", "uwu", ">w<", ":3", "xD", "^^", "owo?", 
            "uwu?", "hehe", "hoho", "yay~", "nice!", "wow!"
        ]
        
        print_banner()

    async def show_help(self, message):
        help_text = """
``` OWO BOT HELP MENU

CONTROL:
start - Start grinding bot
!stop - Stop grinding bot  
stats - Show grinding statistics
!owocmdstats - Show command status

TIME SCHEDULING:
!time set HH:MM AM/PM - Set auto stop time
!time clear - Clear scheduled stop
!time status - Check auto stop status

COMMAND TOGGLE:
!owohunt on/off - Toggle hunt commands
!owobattle on/off - Toggle battle commands  
!owopray on/off - Toggle pray commands
!owo on/off - Toggle owo commands

INFORMATION:
!help - Show this help message
```
`Created by Aditya • Type !help for assistance`
"""
        await message.channel.send(help_text)

    def parse_time(self, time_str):
        try:
            time_obj = datetime.strptime(time_str.upper(), '%I:%M %p')
            now = datetime.now()
            scheduled_time = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)
            return scheduled_time
        except ValueError:
            return None

    async def check_scheduled_stop(self):
        while True:
            if self.auto_stop_enabled and self.scheduled_stop_time and self.running:
                now = datetime.now()
                if now >= self.scheduled_stop_time:
                    channel = self.get_channel(self.channel_id)
                    if channel:
                        await channel.send("🕒 AUTO STOP: Scheduled time reached! Bot stopping automatically.")
                    await self.stop_bot()
                    self.auto_stop_enabled = False
                    self.scheduled_stop_time = None
                    break
            await asyncio.sleep(30)

    def get_random_human_message(self):
        message_type = random.choice(["text", "emoji", "action", "combo"])
        
        if message_type == "text":
            return random.choice(self.random_texts)
        elif message_type == "emoji":
            return random.choice(self.random_emojis)
        elif message_type == "action":
            return random.choice(self.random_actions)
        else:
            parts = []
            if random.random() > 0.5:
                parts.append(random.choice(self.random_texts))
            if random.random() > 0.5:
                parts.append(random.choice(self.random_emojis))
            if random.random() > 0.3:
                parts.append(random.choice(self.random_actions))
            return " ".join(parts)

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def generate_stats_text(self):
        total = sum(cmd["count"] for cmd in self.commands.values())
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        time_since_pray = time.time() - self.commands['pray']['last_used']
        pray_cooldown = max(0, self.commands['pray']['cooldown'] - time_since_pray)
        pray_min = int(pray_cooldown // 60)
        pray_sec = int(pray_cooldown % 60)
        
        uptime_hours = max(1, uptime.total_seconds() / 3600)
        cph = int(total / uptime_hours)
        
        status_color = Fore.GREEN if self.running else Fore.RED
        status_text = "RUNNING" if self.running else "STOPPED"
        
        captcha_status = Fore.RED + "DETECTED" if self.captcha_detected else Fore.GREEN + "ACTIVE"
        
        daily_status = Fore.GREEN + "CLAIMED" if self.daily_claimed else Fore.YELLOW + "PENDING"
        
        auto_stop_info = ""
        if self.auto_stop_enabled and self.scheduled_stop_time:
            time_left = self.scheduled_stop_time - datetime.now()
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            auto_stop_info = f"\n{Fore.YELLOW}🔹 {Fore.CYAN}Auto Stop: {self.scheduled_stop_time.strftime('%I:%M %p')} ({hours_left}h {minutes_left}m left)"
        
        return f"""
{Fore.YELLOW}⚡ {Fore.RED}LIVE GRINDING STATS {Fore.YELLOW}⚡{Fore.CYAN}
╔════════════════════════════════╗
║ {Fore.GREEN}🦊 ᴏᴡᴏ ʜᴜɴᴛ:    {self.commands['hunt']['count']:>3} {Fore.CYAN}         
║ {Fore.RED}⚔️ ᴏᴡᴏ ʙᴀᴛᴛʟᴇ:   {self.commands['battle']['count']:>3} {Fore.CYAN}         
║ {Fore.BLUE}🙏 ᴏᴡᴏ ᴘʀᴀʏ:    {self.commands['pray']['count']:>3}  {Fore.CYAN}         
║ {Fore.MAGENTA}🦉 ᴏᴡᴏs:        {self.commands['owo']['count']:>3}     {Fore.CYAN}         
║ {Fore.YELLOW}📅 ᴏᴡᴏ ᴅᴀɪʟʏ:   {self.commands['daily']['count']:>3}     {Fore.CYAN}         
╠════════════════════════════════╣
║ {Fore.YELLOW}📊 Total:    {total:>8} {Fore.CYAN}        
║ {Fore.CYAN}⏱️ Uptime:  {hours:02d}h {minutes:02d}m {seconds:02d}s        
║ {Fore.CYAN}🚀 Cmd/Hour: {cph:>8} {Fore.CYAN}        
╠════════════════════════════════╣
║ {Fore.CYAN}👤 Name:     {getattr(self.user, 'name', 'N/A')}
║ {Fore.CYAN}📛 Username: @{getattr(self.user, 'name', 'N/A')}#{getattr(self.user, 'discriminator', 'N/A')}
║ {Fore.CYAN}🆔 User ID:  {getattr(self.user, 'id', 'N/A')}
╠════════════════════════════════╣
{Style.RESET_ALL}

{Fore.YELLOW}🔹 {status_color}Current Status: {status_text}
{Fore.YELLOW}🔹 {Fore.RED}Next Pray: {pray_min:02d}m {pray_sec:02d}s
{Fore.YELLOW}🔹 {Fore.GREEN}Daily Status: {daily_status}
{Fore.YELLOW}🔹 {Fore.RED}Captcha Status: {captcha_status}{auto_stop_info}{Style.RESET_ALL}
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

    async def claim_daily_reward(self):
        if not self.daily_claimed:
            channel = self.get_channel(self.channel_id)
            if channel:
                await channel.send("owo daily")
                self.commands["daily"]["count"] += 1
                self.commands["daily"]["last_used"] = time.time()
                self.daily_claimed = True
                animate_text(f"{Fore.GREEN}✅ ᴏᴡᴏ ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅ ᴄʟᴀɪᴍᴇᴅ{Style.RESET_ALL}")
                await asyncio.sleep(5)

    async def on_ready(self):
        animate_text(f"\n{Fore.GREEN}✅ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ {self.user}")
        animate_text(f"{Fore.YELLOW}⚡ ѕᴛᴀʀᴛɪɴɢ ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ....")
        await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="😈 ᴡᴀᴋᴇ ᴜᴘ ᴛᴏ ʀᴇᴀʟɪᴛʏ"))
        
        await self.claim_daily_reward()
        
        if self.running:
            self.spam_task = asyncio.create_task(self.spam_commands())
            self.stats_task = asyncio.create_task(self.show_stats())
            self.time_check_task = asyncio.create_task(self.check_scheduled_stop())
            animate_text(f"{Fore.GREEN}🚀 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕᴛᴀʀᴛᴇᴅ{Style.RESET_ALL}")

    async def send_webhook_alert(self, message):
        current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = {
            "title": "⚠️ ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ ⚠️",
            "description": f"**👤 ᴏᴡᴏ ѕᴄʀɪᴘᴛ ᴏᴡɴᴇʀ:** {self.user.mention if self.user else 'N/A'}\n**🚨 ᴄᴀᴘᴛᴄʜᴀ sᴇɴᴅᴇʀ:** {message.author.mention}\n**📺 ᴄʜᴀɴɴᴇʟ:** {message.channel.mention}\n\n**📊 ʟᴀѕᴛ ᴛɪᴍᴇ ѕᴛᴀᴛѕ**\n🦊 ᴏᴡᴏ ʜᴜɴᴛ: `{self.commands['hunt']['count']}`\n⚔️ ᴏᴡᴏ ʙᴀᴛᴛʟᴇ: `{self.commands['battle']['count']}`\n🙏 ᴏᴡᴏ ᴘʀᴀʏ: `{self.commands['pray']['count']}`\n📅 ᴏᴡᴏ ᴅᴀɪʟʏ: `{self.commands['daily']['count']}`\n⏱️ ᴜᴘᴛɪᴍᴇ: `{hours}h {minutes}m {seconds}s`\n\n**ᴠᴇʀɪғʏ ʟɪɴᴋ:** [ᴄʟɪᴄᴋ ʜᴇʀᴇ](https://owobot.com/captcha)\n\n**ᴍᴇѕѕᴀɢᴇ ᴅᴇᴛᴇᴄᴛᴇᴅ:**\n```\n{message.content}\n```",
            "color": 16711680,
            "footer": {
                "text": f"ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴀʟᴇʀᴛ • {current_time}"
            }
        }
        
        avatar = str(self.user.avatar.url) if self.user and self.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        try:
            requests.post(self.webhook_url, json={
                "content": f"{self.user.mention if self.user else 'Bot'}",
                "embeds": [embed],
                "username": "ᴏᴡᴏ ᴄᴀᴘᴛᴄʜᴀ ᴀʟᴇʀᴛ",
                "avatar_url": avatar
            })
        except:
            pass

    async def handle_captcha(self, message):
        self.captcha_detected = True
        await self.send_webhook_alert(message)
        if os.name == 'posix':
            os.system('termux-vibrate -d 1000 &')
            os.system('termux-toast -b red -c white "⚠️ CAPTCHA DETECTED!" &')
        await self.stop_bot()

    async def stop_bot(self):
        self.running = False
        if self.spam_task:
            self.spam_task.cancel()
        if self.stats_task:
            self.stats_task.cancel()
        if self.time_check_task:
            self.time_check_task.cancel()
        await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="⚠️ STOPPED"))

    async def start_bot(self):
        self.running = True
        self.captcha_detected = False
        self.start_time = datetime.now()
        self.spam_task = asyncio.create_task(self.spam_commands())
        self.stats_task = asyncio.create_task(self.show_stats())
        self.time_check_task = asyncio.create_task(self.check_scheduled_stop())
        await self.change_presence(status=discord.Status.idle, activity=discord.Game(name="😈 ᴡᴀᴋᴇ ᴜᴘ ᴛᴏ ʀᴇᴀʟɪᴛʏ"))

    async def on_message(self, message):
        if message.channel.id == self.channel_id and any(word in message.content.lower() for word in self.suspicious_words):
            if not ("owo battle" in message.content.lower() and "⚠️" in message.content):
                if self.running:
                    await self.handle_captcha(message)
                return

        if message.content.lower() == "!help":
            await self.show_help(message)
            return

        if message.content.lower().strip() == "start":
            if not self.running:
                await self.start_bot()
                await message.channel.send("🚀 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕᴛᴀʀᴛᴇᴅ")
                animate_text(f"\n{Fore.GREEN}🚀 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕᴛᴀʀᴛᴇᴅ by {message.author.name}")
            else:
                await message.channel.send("ℹ️ ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ᴀʟʀᴇᴀᴅʏ ѕᴛᴀʀᴛᴇᴅ")
            return

        if message.content.lower().startswith("!time set "):
            if message.author.id != self.user.id:
                return
                
            time_str = message.content[10:].strip()
            scheduled_time = self.parse_time(time_str)
            
            if scheduled_time:
                self.scheduled_stop_time = scheduled_time
                self.auto_stop_enabled = True
                
                time_left = scheduled_time - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                
                await message.channel.send(f"🕒 AUTO STOP SET: Bot will stop automatically at {scheduled_time.strftime('%I:%M %p')} ({hours_left}h {minutes_left}m from now)")
                
                if self.time_check_task:
                    self.time_check_task.cancel()
                self.time_check_task = asyncio.create_task(self.check_scheduled_stop())
            else:
                await message.channel.send("❌ Invalid time format! Use: !time set 6:30 AM or !time set 9:45 PM")
            return

        if message.content.lower() == "!time clear":
            if message.author.id != self.user.id:
                return
                
            if self.auto_stop_enabled:
                self.auto_stop_enabled = False
                self.scheduled_stop_time = None
                if self.time_check_task:
                    self.time_check_task.cancel()
                await message.channel.send("✅ AUTO STOP CLEARED: Scheduled stop time has been removed")
            else:
                await message.channel.send("ℹ️ No scheduled stop time is set")
            return

        if message.content.lower() == "!time status":
            if message.author.id != self.user.id:
                return
                
            if self.auto_stop_enabled and self.scheduled_stop_time:
                time_left = self.scheduled_stop_time - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                await message.channel.send(f"🕒 AUTO STOP: Scheduled for {self.scheduled_stop_time.strftime('%I:%M %p')} ({hours_left}h {minutes_left}m left)")
            else:
                await message.channel.send("ℹ️7 No auto stop time is currently set")
            return

        if message.author.id != self.user.id:
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
                await message.channel.send("✅ OwO Pray commands enabled")
            elif state == "off":
                self.commands["pray"]["active"] = False
                await message.channel.send("❌ OwO Pray commands disabled")
            return

        if message.content.lower().startswith("!owo "):
            state = message.content.lower().split()[1]
            if state == "on":
                self.commands["owo"]["active"] = True
                await message.channel.send("✅ OwO commands enabled")
            elif state == "off":
                self.commands["owo"]["active"] = False
                await message.channel.send("❌ OwO commands disabled")
            return

        if message.content.lower() == "stats":
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            total_cmds = sum(cmd["count"] for cmd in self.commands.values())

            auto_stop_info = ""
            if self.auto_stop_enabled and self.scheduled_stop_time:
                time_left = self.scheduled_stop_time - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                auto_stop_info = f"\nAuto Stop: {self.scheduled_stop_time.strftime('%I:%M %p')} ({hours_left}h {minutes_left}m left)"

            stats_msg = f"```\n         📊 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕᴛᴀᴛѕ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🦊 ᴏᴡᴏ ʜᴜɴᴛs   | {self.commands['hunt']['count']}\n⚔️ ᴏᴡᴏ ʙᴀᴛᴛʟᴇ  | {self.commands['battle']['count']}\n🙏 ᴏᴡᴏ ᴘʀᴀʏ    | {self.commands['pray']['count']}\n🦉 OwO         | {self.commands['owo']['count']}\n📅 ᴏᴡᴏ ᴅᴀɪʟʏ  | {self.commands['daily']['count']}\n📊 Total       | {total_cmds}\n🕒 Uptime      | {hours}h {minutes}m {seconds}s{auto_stop_info}\n📅 Started     | {self.start_time.strftime('%Y-%m-%d %I:%M %p')}\n👤 User        | {getattr(self.user, 'name', 'N/A')}\n🆔 User ID     | {getattr(self.user, 'id', 'N/A')}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n```"
            await message.channel.send(stats_msg)
            return

        if message.content.lower() == "!owocmdstats":
            stats = f"```\nOwO Command Status:\n━━━━━━━━━━━━━━━━━━━\nHunt   : {'✅ ON' if self.commands['hunt']['active'] else '❌ OFF'}        ʟᴏᴡ ʀɪѕᴋ\nBattle : {'✅ ON' if self.commands['battle']['active'] else '❌ OFF'}      ʟᴏᴡ ʀɪѕᴋ\nPray   : {'✅ ON' if self.commands['pray']['active'] else '❌ OFF'}         ᴍᴇᴅɪᴜᴍ ʀɪѕᴋ\nOwO    : {'✅ ON' if self.commands['owo']['active'] else '❌ OFF'}       ʜɪɢʜ ʀɪѕᴋ\nDaily  : {'✅ CLAIMED' if self.daily_claimed else '❌ PENDING'}   ᴏɴᴇ-ᴛɪᴍᴇ\n━━━━━━━━━━━━━━━━━━━\n```"
            await message.channel.send(stats)
            return

        if message.content.lower() == "!stop":
            if self.running:
                await self.stop_bot()
                await message.channel.send("🚨 ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ѕᴛᴏᴘᴘᴇᴅ")
            else:
                await message.channel.send("ℹ️ ᴏᴡᴏ ɢʀɪɴᴅɪɴɢ ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴛᴏᴘᴘᴇᴅ!")
            return

        if message.content.lower() == "owo inv":
            return

    async def spam_commands(self):
        channel = self.get_channel(self.channel_id)
        while self.running:
            try:
                if random.random() < 0.15:
                    human_msg = self.get_random_human_message()
                    await channel.send(human_msg)
                    await asyncio.sleep(random.uniform(1.0, 3.0))

                if self.commands["hunt"]["active"]:
                    await channel.send("owo hunt")
                    self.commands["hunt"]["count"] += 1
                    await asyncio.sleep(random.randint(11, 13))

                if self.commands["battle"]["active"]:
                    await channel.send("owo battle")
                    self.commands["battle"]["count"] += 1
                    await asyncio.sleep(random.randint(11, 13))

                if (self.commands["pray"]["active"] and time.time() - self.commands["pray"]["last_used"] >= self.commands["pray"]["cooldown"]):
                    await channel.send("owo pray")
                    self.commands["pray"]["count"] += 1
                    self.commands["pray"]["last_used"] = time.time()
                    self.commands["pray"]["cooldown"] = random.randint(300, 360)
                    await asyncio.sleep(random.randint(5, 8))

                if self.commands["owo"]["active"]:
                    await channel.send("owo")
                    self.commands["owo"]["count"] += 1
                    await asyncio.sleep(random.randint(11, 13))

            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                await asyncio.sleep(5)

client = OwoBot()
client.run(TOKEN)
