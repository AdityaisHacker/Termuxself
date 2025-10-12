import discord
from discord.ext import commands
import aiohttp
import os

# Simple Token system (no y/n)
def get_token():
    if os.path.exists("token.txt"):
        with open("token.txt", "r") as f:
            token = f.read().strip()
        if token:
            return token
    token = input("📝 Enter your Discord Token: ").strip()
    with open("token.txt", "w") as f:
        f.write(token)
    return token

TOKEN = get_token()
PREFIX = "!"
bot = commands.Bot(command_prefix=PREFIX, self_bot=True)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def copy(ctx, member: discord.Member = None):
    member = member or ctx.author
    url = member.display_avatar.url
    ext = "gif" if member.display_avatar.is_animated() else "png"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Failed to fetch profile picture.")
            data = await resp.read()

    filename = f"pfp.{ext}"
    with open(filename, "wb") as f:
        f.write(data)

    await ctx.send(file=discord.File(filename))
    os.remove(filename)

@bot.command()
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = await bot.fetch_user(member.id)

    if user.banner is None:
        return await ctx.send("❌ This user has no banner.")

    ext = "gif" if user.banner.is_animated() else "png"
    url = user.banner.url

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Failed to fetch banner.")
            data = await resp.read()

    filename = f"banner.{ext}"
    with open(filename, "wb") as f:
        f.write(data)

    await ctx.send(file=discord.File(filename))
    os.remove(filename)

@bot.command()
async def serverbanner(ctx):
    guild = ctx.guild

    if guild.banner is None:
        return await ctx.send("❌ This server has no banner.")

    ext = "gif" if guild.banner.is_animated() else "png"
    url = guild.banner.url

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Failed to fetch server banner.")
            data = await resp.read()

    filename = f"server_banner.{ext}"
    with open(filename, "wb") as f:
        f.write(data)

    await ctx.send(file=discord.File(filename))
    os.remove(filename)

@bot.command()
async def servercopy(ctx):
    guild = ctx.guild
    files = []

    if guild.icon:
        ext = "gif" if guild.icon.is_animated() else "png"
        url = guild.icon.url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    fname = f"server_icon.{ext}"
                    with open(fname, "wb") as f:
                        f.write(data)
                    files.append(discord.File(fname))

    if guild.banner:
        ext = "gif" if guild.banner.is_animated() else "png"
        url = guild.banner.url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    fname = f"server_banner.{ext}"
                    with open(fname, "wb") as f:
                        f.write(data)
                    files.append(discord.File(fname))

    await ctx.send(f"**Server Name:** `{guild.name}`")
    if files:
        await ctx.send(files=files)

    # Clean-up temporary files
    for f in os.listdir():
        if f.startswith("server_icon") or f.startswith("server_banner"):
            os.remove(f)

bot.run(TOKEN)