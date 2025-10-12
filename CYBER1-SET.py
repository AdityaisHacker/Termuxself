import discord
import asyncio
import os
import random

TOKEN_FILE = "token.txt"
CHANNELS_FILE = "channels.txt"

PREFIX = "!"
OWNER_IDS = [1352765328450654248]
current_message = ""
running = False
spam_tasks = []
send_counts = {}
random_numbers = {}

def load_channels():
    channels = {}
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    channel_id, delay = parts
                    channels[int(channel_id)] = int(delay)
    return channels

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        for channel_id, delay in channels.items():
            f.write(f"{channel_id} {delay}\n")

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    else:
        new_token = input("Enter your token: ").strip()
        with open(TOKEN_FILE, "w") as f:
            f.write(new_token)
        return new_token

TOKEN = get_token()
CHANNELS = load_channels()

client = discord.Client()

@client.event
async def on_ready():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"✅ Logged in as {client.user}")
    print("Bot is running...")

@client.event
async def on_message(message):
    global running, current_message, spam_tasks, random_numbers

    if message.author.id not in OWNER_IDS:
        return

    if message.content.startswith(PREFIX):
        # Set Message
        if message.content.startswith(f"{PREFIX}set "):
            new_msg = message.content[len(f"{PREFIX}set "):].strip()
            if new_msg:
                current_message = new_msg
                await message.channel.send(f"✅ Message updated:\n{new_msg}")

        # Start Spam
        elif message.content.lower() == f"{PREFIX}start":
            if not running:
                running = True
                if not CHANNELS:
                    await message.channel.send("⚠️ No channels added!")
                    return
                
                spam_tasks = []
                for channel_id, delay in CHANNELS.items():
                    task = asyncio.create_task(spam_channel(channel_id, delay))
                    spam_tasks.append(task)
                await message.channel.send("▶️ Spam started.")

        # Stop Spam
        elif message.content.lower() == f"{PREFIX}stop":
            if running:
                running = False
                for task in spam_tasks:
                    task.cancel()
                spam_tasks.clear()
                await message.channel.send("⛔ Spam stopped.")

        # Show Stats
        elif message.content.lower() == f"{PREFIX}stats":
            stats_lines = []
            total = 0
            sorted_channels = sorted(send_counts.items(), key=lambda x: x[1], reverse=True)
            for channel_id, count in sorted_channels:
                channel = client.get_channel(channel_id)
                name = channel.name if channel else "Unknown"
                bar = "█" * (count // 5)
                stats_lines.append(f"📢 {name} | {count} msgs {bar}")
                total += count
            
            stats_lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")
            stats_lines.append(f"🔧 Total Channels: {len(send_counts)}")
            stats_lines.append(f"📨 Total Messages: {total}")
            stats_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")

            await message.channel.send(f"{message.author.mention} stats:\n```ansi\n\u001b[33m" + "\n".join(stats_lines) + "\u001b[0m```")

        # Show Channels
        elif message.content.lower() == f"{PREFIX}channels":
            if not CHANNELS:
                reply = await message.channel.send("⚠️ No channels added.")
                await asyncio.sleep(40)
                await reply.delete()
                await message.delete()
            else:
                random_numbers.clear()
                sent_msg = await message.channel.send("> Loading channels...")
                await asyncio.sleep(1)
                text = ""
                for idx, (channel_id, delay) in enumerate(CHANNELS.items()):
                    random_id = random.randint(1000, 9999)
                    while random_id in random_numbers:
                        random_id = random.randint(1000, 9999)
                    random_numbers[random_id] = channel_id

                    channel = client.get_channel(channel_id)
                    name = channel.name if channel else "Unknown"
                    text += f"> ``{name}`` |``{channel_id}``| Time: ``{delay}s`` |``{random_id}``\n"
                    if idx % 5 == 0:
                        await sent_msg.edit(content=text)
                        await asyncio.sleep(0.7)

                await sent_msg.edit(content=text)
                await asyncio.sleep(60)
                await sent_msg.delete()
                await message.delete()

        # Add Channel
        elif message.content.lower().startswith(f"{PREFIX}add"):
            parts = message.content.split()
            if len(parts) < 3:
                msg = await message.channel.send("❌ Usage: !add <channel_id> <time_in_seconds>")
                await asyncio.sleep(40)
                await msg.delete()
                await message.delete()
                return
            
            try:
                channel_id = int(parts[1])
                time_value = parts[2]
                delay = int(time_value[:-1]) * (60 if time_value.endswith('m') else 1)

                if delay < 35:
                    warn = await message.channel.send("❌ Minimum delay must be 35 seconds to avoid rate limit.")
                    await asyncio.sleep(40)
                    await warn.delete()
                    await message.delete()
                    return

                CHANNELS[channel_id] = delay
                save_channels(CHANNELS)
                confirm = await message.channel.send(f"✅ Channel {channel_id} added with {delay}s delay.")
                await asyncio.sleep(40)
                await confirm.delete()
                await message.delete()
            except Exception as e:
                print(f"⚠️ Error adding channel: {e}")

        # Remove Channel
        elif message.content.lower().startswith(f"{PREFIX}remove"):
            parts = message.content.split()
            if len(parts) < 2:
                msg = await message.channel.send("❌ Usage: !remove <random_number/channel_id>")
                await asyncio.sleep(40)
                await msg.delete()
                await message.delete()
                return

            key = parts[1]
            removed = False

            if key.isdigit():
                num = int(key)

                if num in random_numbers:
                    channel_id = random_numbers[num]
                    if channel_id in CHANNELS:
                        del CHANNELS[channel_id]
                        save_channels(CHANNELS)
                        removed = True

                elif num in CHANNELS:
                    del CHANNELS[num]
                    save_channels(CHANNELS)
                    removed = True

            if removed:
                confirm = await message.channel.send(f"✅ Channel removed.")
                await asyncio.sleep(40)
                await confirm.delete()
                await message.delete()
            else:
                warn = await message.channel.send("❌ Channel not found.")
                await asyncio.sleep(40)
                await warn.delete()
                await message.delete()

        # Help Command
        elif message.content.lower() == f"{PREFIX}help":
            commands_list = [
                {"command": "> 📝 !set <message>", "description": "``Sets the message to spam.``"},
                {"command": "> ▶️ !start", "description": "``Starts the spam.``"},
                {"command": "> 🛑 !stop", "description": "``Stops the spam.``"},
                {"command": "> 📉 !stats", "description": "``Displays stats.``"},
                {"command": "> 📓 !channels", "description": "``Shows all added channels.``"},
                {"command": "> 🏔 !add <channel_id> <time>", "description": "``Adds a channel.``"},
                {"command": "> 🎃 !remove <id>", "description": "``Removes a channel.``"},
            ]

            cmd_text = "``Here is the list of all available commands:``\n"
            for cmd in commands_list:
                cmd_text += f"**{cmd['command']}**: {cmd['description']}\n\n"

            await message.channel.send(cmd_text)

async def spam_channel(channel_id, delay):
    await client.wait_until_ready()
    channel = client.get_channel(channel_id)
    send_counts[channel_id] = 0
    while running:
        try:
            await channel.send(current_message)
            send_counts[channel_id] += 1
            print(f"Sent to {channel.name} | {send_counts[channel_id]} messages")
        except Exception as e:
            print(f"⚠️ Error sending to {channel_id}: {e}")
        await asyncio.sleep(delay)

client.run(TOKEN)
