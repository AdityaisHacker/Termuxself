import discord
from discord.ext import commands
import asyncio
import os
import aiohttp

OWNER_ID = 1352765328450654248
TARGET_CHANNEL_ID = 1364678037702185050
cloning_in_progress = False

def get_token():
    if os.path.exists("token.txt"):
        with open("token.txt", "r") as f:
            token = f.read().strip()
        if token:
            return token
    new_token = input("📂 Please enter the token: ").strip()
    with open("token.txt", "w") as f:
        f.write(new_token)
    return new_token

TOKEN = get_token()
bot = commands.Bot(command_prefix="!", self_bot=True)
bot.remove_command("help")

saved_structure = []
saved_roles = []
saved_icon_url = None
saved_name = None

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} | ID: {bot.user.id}")

@bot.command()
async def server(ctx, arg=None, server_id: int = None):
    global cloning_in_progress, saved_icon_url, saved_name

    if ctx.author.id != OWNER_ID:
        return

    target = bot.get_channel(TARGET_CHANNEL_ID)
    if not target:
        await ctx.send("❌ Invalid target channel.")
        return

    if arg == "save":
        guild = ctx.guild
        structure = []

        saved_name = guild.name
        saved_icon_url = guild.icon.url if guild.icon else None

        for category in guild.categories:
            cat_data = {"type": "category", "name": category.name, "channels": []}
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel):
                    cat_data["channels"].append({"type": "text", "name": channel.name})
                elif isinstance(channel, discord.VoiceChannel):
                    cat_data["channels"].append({"type": "voice", "name": channel.name})
            structure.append(cat_data)

        for channel in guild.channels:
            if not channel.category:
                if isinstance(channel, discord.TextChannel):
                    structure.append({"type": "text", "name": channel.name, "category": None})
                elif isinstance(channel, discord.VoiceChannel):
                    structure.append({"type": "voice", "name": channel.name, "category": None})

        saved_structure.clear()
        saved_structure.extend(structure)

        saved_roles.clear()
        for role in guild.roles:
            if role.name != "@everyone":
                saved_roles.append({
                    "name": role.name,
                    "permissions": role.permissions.value,
                    "color": role.color.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable
                })

        text_output = f"📌 Server Name: {guild.name}\n🆔 ID: {guild.id}\n\n"
        for item in structure:
            if item["type"] == "category":
                text_output += f"\n📁 Category: {item['name']}\n"
                for ch in item["channels"]:
                    symbol = "💬" if ch["type"] == "text" else "🔊"
                    text_output += f"  └─ {symbol} {ch['name']}\n"
            else:
                symbol = "💬" if item["type"] == "text" else "🔊"
                text_output += f"\n{symbol} {item['name']} (No Category)\n"

        for chunk in [text_output[i:i+1900] for i in range(0, len(text_output), 1900)]:
            await target.send(f"```{chunk}```")

        await target.send("✅ Server structure, icon, and roles saved!")

    elif arg == "clone" and server_id:
        if cloning_in_progress:
            await target.send("⚠️ Cloning already in progress. Wait for it to finish.")
            return

        if not saved_structure:
            await target.send("⚠️ No saved structure found! Use `!server save` first.")
            return

        target_guild = bot.get_guild(server_id)
        if not target_guild:
            await target.send("❌ Bot is not in the target server or invalid ID.")
            return

        try:
            cloning_in_progress = True

            # Clone icon and name
            icon_bytes = None
            if saved_icon_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(saved_icon_url) as resp:
                        if resp.status == 200:
                            icon_bytes = await resp.read()

            await target_guild.edit(
                name=saved_name,
                icon=icon_bytes if icon_bytes else None
            )

            # Clone roles
            for role_data in saved_roles:
                await target_guild.create_role(
                    name=role_data["name"],
                    permissions=discord.Permissions(role_data["permissions"]),
                    colour=discord.Colour(role_data["color"]),
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
                await asyncio.sleep(1)

            # Clone channels
            cat_map = {}
            for item in saved_structure:
                if item["type"] == "category":
                    new_cat = await target_guild.create_category(item["name"])
                    cat_map[item["name"]] = new_cat
                    await asyncio.sleep(1)

                    for ch in item["channels"]:
                        if ch["type"] == "text":
                            await new_cat.create_text_channel(ch["name"])
                        elif ch["type"] == "voice":
                            await new_cat.create_voice_channel(ch["name"])
                        await asyncio.sleep(1)

                elif item.get("category") is None:
                    if item["type"] == "text":
                        await target_guild.create_text_channel(item["name"])
                    elif item["type"] == "voice":
                        await target_guild.create_voice_channel(item["name"])
                    await asyncio.sleep(1)

            await target.send("✅ Server cloned with icon, name, roles, and channels!")
        except Exception as e:
            await target.send(f"❌ Error during cloning: {e}")
        finally:
            cloning_in_progress = False

    elif arg == "clear":
        guild = ctx.guild

        for channel in guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Failed to delete channel {channel.name}: {e}")

        for role in guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Failed to delete role {role.name}: {e}")

        await target.send("✅ All channels and roles cleared from the server.")

    else:
        await target.send("❌ Usage: `!server save`, `!server clone <server_id>`, or `!server clear`")


bot.run(TOKEN)
