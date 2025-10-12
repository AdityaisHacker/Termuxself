import discord
import asyncio
import subprocess
import os
from discord.ext import commands

# Global dictionary to track script processes
scripts = {
    "ADITYA1-SET": {"file": "CYBER1-SET.py", "process": None, "status": "🔴 Stopped"},
    "ADITYA2-CLONE": {"file": "CYBER2-CLONE.py", "process": None, "status": "🔴 Stopped"},
    "ADITYA3-DM": {"file": "CYBER3-DM.py", "process": None, "status": "🔴 Stopped"},
    "ADITYA4-OWO": {"file": "CYBER4-OWO.py", "process": None, "status": "🔴 Stopped"},
    "ADITYA5-AVATAR": {"file": "CYBER5-AVATAR.py", "process": None, "status": "🔴 Stopped"},
    "ADITYA6-TOKEN": {"file": "dcid.py", "process": None, "status": "🔴 Stopped"},
}

# Status tracking variables
current_status = {
    "status_type": "online",
    "activities": ["Html/CSS/Python", "", "", ""],
    "current_activity_index": 0
}

# Disable the default help command
bot = commands.Bot(
    command_prefix="!", 
    self_bot=True,
    help_command=None  # This disables the built-in help command
)

# Load token from token.txt
def load_token():
    try:
        with open("token.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("❌ token.txt file not found!")
        return None

TOKEN = load_token()

if TOKEN is None:
    print("❌ No valid token found. Exiting bot.")
    exit()

def save_status():
    """Save current status to a file"""
    try:
        with open("status_backup.txt", "w") as f:
            for name, data in scripts.items():
                status = "🟢 Running" if data["process"] and data["process"].poll() is None else "🔴 Stopped"
                f.write(f"SCRIPT:{name}:{status}\n")
            
            f.write(f"BOT_STATUS:{current_status['status_type']}\n")
            f.write(f"CURRENT_ACTIVITY_INDEX:{current_status['current_activity_index']}\n")
            for i, activity in enumerate(current_status['activities']):
                f.write(f"ACTIVITY_{i}:{activity}\n")
    except Exception as e:
        print(f"Error saving status: {e}")

def load_status():
    """Load status from backup file"""
    try:
        if os.path.exists("status_backup.txt"):
            with open("status_backup.txt", "r") as f:
                for line in f.readlines():
                    parts = line.strip().split(":")
                    if len(parts) >= 2:
                        if parts[0] == "SCRIPT" and len(parts) == 3:
                            name, status = parts[1], parts[2]
                            if name in scripts:
                                scripts[name]["status"] = status
                        elif parts[0] == "BOT_STATUS":
                            current_status["status_type"] = parts[1]
                        elif parts[0] == "CURRENT_ACTIVITY_INDEX":
                            current_status["current_activity_index"] = int(parts[1])
                        elif parts[0].startswith("ACTIVITY_"):
                            index = int(parts[0].split("_")[1])
                            if index < 4:
                                current_status["activities"][index] = ":".join(parts[1:])
    except Exception as e:
        print(f"Error loading status: {e}")

def get_status_enum(status_type):
    """Convert string status to discord.Status enum"""
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible
    }
    return status_map.get(status_type, discord.Status.online)

async def update_presence():
    """Update bot's presence with saved status"""
    current_activity_text = current_status["activities"][current_status["current_activity_index"]]
    if current_activity_text:
        activity = discord.Game(name=current_activity_text)
        status = get_status_enum(current_status["status_type"])
        await bot.change_presence(activity=activity, status=status)
    else:
        status = get_status_enum(current_status["status_type"])
        await bot.change_presence(activity=None, status=status)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    load_status()
    await update_presence()
    current_activity = current_status["activities"][current_status["current_activity_index"]]
    print(f"Status restored: {current_status['status_type']} - Activity {current_status['current_activity_index'] + 1}: {current_activity}")
    bot.loop.create_task(status_saver())

@bot.event
async def on_resumed():
    """When connection is resumed"""
    print("Connection resumed - restoring status...")
    await update_presence()

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors silently"""
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        pass

async def status_saver():
    """Background task to save status periodically"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(30)
        save_status()

@bot.command()
async def status(ctx, status_type: str = None):
    """Change bot status (online, idle, dnd, invisible)"""
    if status_type is None:
        current_activity = current_status["activities"][current_status["current_activity_index"]]
        activities_list = "\n".join([f"{i+1}. {activity if activity else '(Empty)'}" for i, activity in enumerate(current_status['activities'])])
        await ctx.send(f"**Current Status:** `{current_status['status_type']}`\n**Current Activity ({current_status['current_activity_index'] + 1}):** `{current_activity}`\n\n**All Activities:**\n{activities_list}")
        return
    
    status_type = status_type.lower()
    valid_statuses = ["online", "idle", "dnd", "invisible"]
    
    if status_type not in valid_statuses:
        await ctx.send(f"❌ Invalid status! Use: `{', '.join(valid_statuses)}`")
        return
    
    current_status["status_type"] = status_type
    await update_presence()
    save_status()
    await ctx.send(f"✅ Status changed to `{status_type}`")

@bot.command()
async def activity(ctx, action: str = None, *, text: str = None):
    """Manage bot's activities (4 slots available)"""
    
    if action is None:
        activities_list = "\n".join([f"{i+1}. {activity if activity else '(Empty)'} {'🟢' if i == current_status['current_activity_index'] else '⚫'}" for i, activity in enumerate(current_status['activities'])])
        await ctx.send(f"**Current Activity Slot:** {current_status['current_activity_index'] + 1}\n\n**Activity Slots:**\n{activities_list}\n\nUse `!activity edit <slot> <text>` to edit or `!activity clear` to clear all")
        return
    
    action = action.lower()
    
    if action == "clear":
        for i in range(4):
            current_status["activities"][i] = ""
        current_status["current_activity_index"] = 0
        await update_presence()
        save_status()
        await ctx.send("✅ All activities cleared!")
    
    elif action == "edit":
        if text is None:
            await ctx.send("❌ Usage: `!activity edit <slot(1-4)> <text>`")
            return
        
        parts = text.split(" ", 1)
        if len(parts) < 2:
            await ctx.send("❌ Usage: `!activity edit <slot(1-4)> <text>`")
            return
        
        try:
            slot = int(parts[0]) - 1
            if slot < 0 or slot > 3:
                await ctx.send("❌ Slot must be between 1 and 4!")
                return
            
            activity_text = parts[1]
            current_status["activities"][slot] = activity_text
            await update_presence()
            save_status()
            await ctx.send(f"✅ Activity slot {slot + 1} updated to: `{activity_text}`")
            
        except ValueError:
            await ctx.send("❌ Invalid slot number! Use 1, 2, 3, or 4")
    
    elif action in ["1", "2", "3", "4"]:
        slot = int(action) - 1
        current_status["current_activity_index"] = slot
        await update_presence()
        save_status()
        activity_text = current_status["activities"][slot] if current_status["activities"][slot] else "(Empty)"
        await ctx.send(f"✅ Switched to activity slot {slot + 1}: `{activity_text}`")
    
    else:
        await ctx.send("""
**Activity Commands:**
- `!activity` - Show all activity slots
- `!activity clear` - Clear all activities
- `!activity edit <slot(1-4)> <text>` - Edit specific activity
- `!activity <1/2/3/4>` - Switch to specific activity slot
        """)

@bot.command(name='script')
async def script_command(ctx, number: str, action: str):
    """Control scripts - !script <number> <on/off>"""
    try:
        number = int(number)
    except ValueError:
        await ctx.send("❌ Invalid number! Please provide a number (e.g. 1, 2, etc.).")
        return
    
    if 1 <= number <= len(scripts):
        script_name = list(scripts.keys())[number - 1]
        await toggle_script(ctx, action.lower(), script_name)
    else:
        await ctx.send(f"⚠️ Invalid script number! Use a number between 1 and {len(scripts)}.")

async def toggle_script(ctx, action, script_name=None):
    if script_name is None:
        try:
            script_name = list(scripts.keys())[int(action) - 1]
        except (IndexError, ValueError):
            await ctx.send(f"⚠️ Invalid script number! Use a number between 1 and {len(scripts)}.")
            return

    script = scripts.get(script_name)
    if not script:
        await ctx.send(f"❌ Script `{script_name}` not found.")
        return

    if action.lower() == "on":
        if script["process"] is None or script["process"].poll() is not None:
            try:
                script["process"] = subprocess.Popen(["python", script["file"]])
                script["status"] = "🟢 Running"
                save_status()
                await ctx.send(f"✅ `{script_name}` started!")
            except Exception as e:
                await ctx.send(f"❌ Error starting `{script_name}`: {str(e)}")
        else:
            await ctx.send(f"⚠️ `{script_name}` is already running!")
    elif action.lower() == "off":
        if script["process"] and script["process"].poll() is None:
            try:
                script["process"].terminate()
                script["process"].wait(timeout=5)
                script["process"] = None
                script["status"] = "🔴 Stopped"
                save_status()
                await ctx.send(f"🛑 `{script_name}` stopped!")
            except Exception as e:
                await ctx.send(f"❌ Error stopping `{script_name}`: {str(e)}")
        else:
            await ctx.send(f"⚠️ `{script_name}` is not running!")
    else:
        await ctx.send("⚙️ Usage: `!script <number> on/off`")

@bot.command(name='scriptstats')
async def scriptstats_command(ctx):
    """Show detailed statistics of all scripts"""
    for name, data in scripts.items():
        if data["process"] and data["process"].poll() is None:
            data["status"] = "🟢 Running"
        else:
            data["status"] = "🔴 Stopped"
    
    current_activity = current_status["activities"][current_status["current_activity_index"]]
    
    stats = "\n\n"
    stats += "```diff\n"
    stats += "               📋  𝙰𝙳𝙸𝚃𝚈𝙰 ѕᴛᴀᴛѕ\n"
    for i, (name, data) in enumerate(scripts.items(), 1):
        status_icon = "🟢" if "Running" in data['status'] else "🔴"
        stats += f"{i}. {name}: {data['status']}\n"
    stats += "\n"
    stats += f"Status: {current_status['status_type']}\n"
    stats += f"Activity: {current_activity if current_activity else '(None)'}\n"
    stats += f"Version: 1.0\n"
    stats += "```\n"
    
    save_status()
    await ctx.send(stats)

try:
    bot.run(TOKEN)
except Exception as e:
    print(f"Bot error: {e}")
    save_status()
