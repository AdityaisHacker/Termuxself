import discord
from discord.ext import commands
import asyncio
import datetime
import os

OWNER_ID = 1201939358928863292
TOKEN_FILE = "token.txt"
CONFIG_FILE = "mode_config.txt"

# Token System (Saved in token.txt)
def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            saved_token = f.read().strip()
        print("Saved token found.")
        return saved_token
    else:
        print("No saved token found. Please add your token to token.txt.")
        exit()

TOKEN = get_token()

# Bot Setup
bot = commands.Bot(command_prefix='!', self_bot=True)
bot.remove_command("help")

# Mode Config Load
dm_mode = False
server_mode = False
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        lines = f.read().splitlines()
        dm_mode = "dm_mode=True" in lines
        server_mode = "server_mode=True" in lines

dm_deleted = {}
group_deleted = {}
server_deleted = {}
start_time = datetime.datetime.now()

def save_config():
    with open(CONFIG_FILE, "w") as f:
        f.write(f"dm_mode={'True' if dm_mode else 'False'}\n")
        f.write(f"server_mode={'True' if server_mode else 'False'}\n")

def get_runtime():
    delta = datetime.datetime.now() - start_time
    return str(delta).split('.')[0]

@bot.event
async def on_ready():
    print(f"Login successful: {bot.user} (ID: {bot.user.id})")
    print("Self-bot is now ready!")

@bot.command()
async def dm(ctx, mode: str = None):
    global dm_mode, server_mode
    if mode == "mode":
        dm_mode = not dm_mode
        server_mode = False if dm_mode else server_mode
        save_config()
        msg = await ctx.send(f"{'✅ DM mode is now ON' if dm_mode else '❌ DM mode is now OFF'}")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def server(ctx, mode: str = None):
    global server_mode, dm_mode
    if mode == "mode":
        server_mode = not server_mode
        dm_mode = False if server_mode else dm_mode
        save_config()
        msg = await ctx.send(f"{'✅ Server mode is now ON' if server_mode else '❌ Server mode is now OFF'}")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def status(ctx):
    await ctx.send(f"DM Mode: {'ON' if dm_mode else 'OFF'}\nServer Mode: {'ON' if server_mode else 'OFF'}")

@bot.command()
async def clear(ctx, amount: int):
    global dm_deleted, group_deleted, server_deleted

    if dm_mode and isinstance(ctx.channel, discord.DMChannel):
        name = str(ctx.channel.recipient)
        dm_deleted[name] = dm_deleted.get(name, 0)
        count = 0
        async for msg in ctx.channel.history(limit=300):
            if msg.author.id == bot.user.id:
                try:
                    await msg.delete()
                    dm_deleted[name] += 1
                    count += 1
                    await asyncio.sleep(2)
                except:
                    pass
                if count >= amount:
                    break
        m = await ctx.send(f"Successfully deleted {count} messages.")
        await asyncio.sleep(2)
        await m.delete()

    elif dm_mode and isinstance(ctx.channel, discord.GroupChannel):
        name = ctx.channel.name or "Unnamed Group"
        group_deleted[name] = group_deleted.get(name, 0)
        count = 0
        async for msg in ctx.channel.history(limit=300):
            if msg.author.id == bot.user.id:
                try:
                    await msg.delete()
                    group_deleted[name] += 1
                    count += 1
                    await asyncio.sleep(2)
                except:
                    pass
                if count >= amount:
                    break
        m = await ctx.send(f"Successfully deleted {count} messages.")
        await asyncio.sleep(3)
        await m.delete()

    elif server_mode and isinstance(ctx.channel, discord.TextChannel):
        name = ctx.channel.name
        server_deleted[name] = server_deleted.get(name, 0)
        count = 0
        async for msg in ctx.channel.history(limit=500):
            if msg.author.id == bot.user.id:
                try:
                    await msg.delete()
                    server_deleted[name] += 1
                    count += 1
                    await asyncio.sleep(2)
                except:
                    pass
                if count >= amount:
                    break
        m = await ctx.send(f"Successfully deleted {count} messages.")
        await asyncio.sleep(3)
        await m.delete()

    else:
        m = await ctx.send("❌ No valid mode is ON or unsupported channel.")
        await asyncio.sleep(3)
        await m.delete()

@bot.command()
async def stats(ctx, mode: str = None):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ Only owner can check stats.")
        return

    if not mode or mode.lower() != "all":
        await ctx.send("❌ Wrong or missing command. Use `!stats all`.") 
        return

    now = datetime.datetime.now().strftime('%I:%M:%S %p')
    runtime = get_runtime()

    message = "```\n"

    for name in dm_deleted:
        message += f"{name} | Deleted Messages: {dm_deleted[name]}\n"
    if dm_deleted:
        message += "------------------------------\n"
        message += "🗑️ DM Delete Stats\n"
        message += f"Mode Status: {'ON' if dm_mode else 'OFF'}\n"
        message += f"Time: {now}\n"
        message += f"Runtime: {runtime}\n"
        message += f"Total Deleted: {sum(dm_deleted.values())}\n\n"

    for name in group_deleted:
        message += f"{name} | Deleted Messages: {group_deleted[name]}\n"
    if group_deleted:
        message += "------------------------------\n"
        message += "🗑️ Group DM Stats\n"
        message += f"Mode Status: {'ON' if dm_mode else 'OFF'}\n"
        message += f"Time: {now}\n"
        message += f"Runtime: {runtime}\n"
        message += f"Total Deleted: {sum(group_deleted.values())}\n\n"

    for name in server_deleted:
        message += f"{name} | Deleted Messages: {server_deleted[name]}\n"
    if server_deleted:
        message += "------------------------------\n"
        message += "🗑️ Server Delete Stats\n"
        message += f"Mode Status: {'ON' if server_mode else 'OFF'}\n"
        message += f"Time: {now}\n"
        message += f"Runtime: {runtime}\n"
        message += f"Total Deleted: {sum(server_deleted.values())}\n\n"

    message += "```"
    sent = await ctx.send(message)
    await asyncio.sleep(180)
    await sent.delete()

bot.run(TOKEN)
