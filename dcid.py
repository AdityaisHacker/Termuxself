import discord
from discord.ext import commands
import requests
import json
import base64
import os
from datetime import datetime

# Token file se read karo
with open('token.txt', 'r') as file:
    USER_TOKEN = file.read().strip()

bot = commands.Bot(command_prefix='!', self_bot=True)

class DiscordTokenGrabber:
    def __init__(self):
        self.base_url = "https://discord.com/api/v9"
        self.session = requests.Session()
        self._configure_session()

    def _configure_session(self):
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Origin': 'https://discord.com',
            'Referer': 'https://discord.com/login',
            'X-Super-Properties': self._generate_super_properties()
        })

    @staticmethod
    def _generate_super_properties():
        props = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "browser_version": "91.0.4472.124",
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 123456,
            "client_event_source": None
        }
        return base64.b64encode(json.dumps(props).encode()).decode()

    def _login(self, email, password):
        login_url = f"{self.base_url}/auth/login"
        
        payload = {
            'login': email,
            'password': password,
            'undelete': False,
            'captcha_key': None,
            'login_source': None,
            'gift_code_sku_id': None
        }
        
        try:
            response = self.session.post(login_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                return token
            else:
                return None
                
        except Exception as e:
            return None

    def _get_user_info(self, token):
        if not token:
            return None
            
        self.session.headers['Authorization'] = token
        try:
            response = self.session.get(f"{self.base_url}/users/@me")
            
            if response.status_code == 200:
                data = response.json()
                creation_date = datetime.fromtimestamp(((int(data['id']) >> 22) + 1420070400000)/1000)
                return {
                    'id': data['id'],
                    'username': data['username'],
                    'discriminator': data['discriminator'],
                    'email': data.get('email'),
                    'phone': data.get('phone'),
                    'mfa_enabled': data.get('mfa_enabled', False),
                    'bot': data.get('bot', False),
                    'created_at': creation_date.strftime("%Y-%m-%d"),
                    'token': token
                }
            else:
                return None
        except Exception as e:
            return None

    def grab_token(self, email, password):
        token = self._login(email, password)
        if not token:
            return None, "❌ Login failed! Check credentials or you might be rate limited."
        
        user_info = self._get_user_info(token)
        if not user_info:
            return None, "❌ Failed to get user info with the token."
        
        return user_info, "✅ Token successfully grabbed!"

@bot.event
async def on_ready():
    print(f'Connected to {bot.user}')

@bot.command()
async def token(ctx, email: str, password: str):
    """Get Discord account token using email and password"""
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    processing_msg = await ctx.send("🔄 Processing your request...")
    
    grabber = DiscordTokenGrabber()
    user_info, message = grabber.grab_token(email, password)
    
    if user_info:
        # Phone ko properly handle karo
        phone_display = user_info['phone'] if user_info['phone'] else '❌ None'
        
        # Emojis ke saath fancy text
        result_text = f"""
```            🎯 TOKEN INFORMATION 🎯

👤 Username: {user_info['username']}#{user_info['discriminator']}
🆔 User ID: {user_info['id']}
📧 Email: {user_info['email']}
📅 Account Created: {user_info['created_at']}
🛡️ 2FA: {'✅ Enabled' if user_info['mfa_enabled'] else '❌ Disabled'}
📱 Phone: {phone_display}
```
                                       🔑 **TOKEN:**
||{user_info['token']}||

`⚠️ Click to reveal token | Keep your token secure!`

"""
        await processing_msg.delete()
        await ctx.send(result_text)
        
    else:
        await processing_msg.delete()
        await ctx.send(f"🚨 **ERROR:** {message}")

@bot.command()
async def cmds(ctx):
    """Show all available commands"""
    help_text = """
📖 **Available Commands:** 📖

`!token <email> <password>` - 🔑 Get account token
`!cmds` - ❓ Show this help message

💡 **Usage Example:**
`!token example@gmail.com password123`

⚡ **Note:** This selfbot is for educational purposes only!
"""
    await ctx.send(help_text)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Usage:** `!token <email> <password>`")
    else:
        await ctx.send(f"🚨 **Error:** {str(error)}")

if __name__ == "__main__":
    try:
        bot.run(USER_TOKEN)
    except Exception as e:
        print(f"Error: {e}")
