import os
import sqlite3
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

def user_exists(user_id):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM messages WHERE userid = ?', (user_id,))
    result = c.fetchone()
    conn.close()

    return result is not None

load_dotenv()
keep_alive()

conn = sqlite3.connect('messages.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        userid INTEGER NOT NULL,
        messageid INTEGER NOT NULL,
        threadid INTEGER NOT NULL
    )
''')

conn.commit()
conn.close()

TOKEN = os.getenv("DISCORD_TOKEN")

SUBMISSIONS_CHANNEL = 1393120849397157899
DISCUSSIONS_CHANNEL = 1375524101858398268
MODERATOR_ROLE = 1371013866212950127
GUILD_ID = 1371013559571583050

bot_deleted_messages = set()

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 

client = commands.Bot(command_prefix="$", intents=intents)

@client.tree.command(name="deletedb", 
                     description="Delete all entries in the database",
                     guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(MODERATOR_ROLE)
async def deletedb(interaction: discord.Interaction):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('DELETE FROM messages')
    conn.commit()
    conn.close()
    await interaction.response.send_message("🗑️ All entries deleted.", ephemeral=True)

@client.tree.command(name="viewdb",
                     description="View the entries present in the database",
                     guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(MODERATOR_ROLE)
async def viewdb(interaction: discord.Interaction):

    # prevent timeout
    await interaction.response.defer(ephemeral=True)

    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('SELECT username, userid, messageid, threadid FROM messages')
    rows = c.fetchall()
    conn.close()

    if not rows:
        await interaction.followup.send(":x: No entries found in the database.", ephemeral=True)
        return

    content = "username, userid, messageid, threadid\n"
    content += "\n".join([f"{row[0]}, {row[1]}, {row[2]}, {row[3]}" for row in rows])

    temp_file = "db_dump.txt"

    with open(temp_file, "w") as f:
        f.write(content)

    await interaction.followup.send("📄 Database entries: ", file=discord.File(temp_file), ephemeral=True)

    # delete the temp file
    os.remove(temp_file)

@client.tree.command(name="removesubmission",
                     description="Delete the submission of an user",
                     guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(MODERATOR_ROLE)
@app_commands.describe(user="User whose submission you want to remove",
                       reason="Reason for deletion (sent to user via DM)")
async def removesubmission(interaction: discord.Interaction, user: discord.Member, reason: str):

    # prevent timeout
    await interaction.response.defer(ephemeral=True)

    conn = sqlite3.connect("messages.db")
    c = conn.cursor()

    c.execute("SELECT id, messageid, threadid FROM messages WHERE userid = ?", (user.id,))
    result = c.fetchone()
    conn.close()

    if not result:
        await interaction.followup.send(":x: No entries found for this user.", ephemeral=True)
        return
    
    id, message_id, thread_id = result

    try:
        channel = interaction.guild.get_channel(SUBMISSIONS_CHANNEL)
        message = await channel.fetch_message(message_id)
        
        bot_deleted_messages.add(message.id)
        await message.delete()

    except Exception as e:
        await interaction.followup.send(f"⚠️ Failed to delete message:\n```{e}```", ephemeral=True)
        return

    try:
        thread = await interaction.guild.fetch_channel(thread_id)
        await thread.delete()
    except Exception as e:
        await interaction.followup.send(f"⚠️ Failed to delete thread:\n```{e}```", ephemeral=True)
        return

    await interaction.followup.send(f"Submission of {user.mention} with ID {id} deleted successfully.", ephemeral=True)

    channel = interaction.guild.get_channel(SUBMISSIONS_CHANNEL)

    try:
        await user.send(f"Your submission for the **SW Meme Event** in <#{SUBMISSIONS_CHANNEL}> is removed by the moderators because of the reason: {reason}.")
    except Exception:
        await channel.send(f"{user.mention} Your submission for the **SW Meme Event** is removed by the moderators because of the reason: {reason}.")

    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE userid = ?", (user.id,))
    conn.commit()
    conn.close()

@client.command()
async def ping(ctx):
    await ctx.channel.send("Pong!")

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

    print("Commands before sync:")
    for cmd in client.tree.get_commands():
        print(cmd.name)

    try:
        guild = discord.Object(id=GUILD_ID)

        synced = await client.tree.sync(guild = guild)
        print(f"Synced {len(synced)} command(s)")

    except Exception as e:
        print(f"Sync error: {e}")

@client.event
async def on_message(message):

    isMedia = False

    if client.user == message.author:
        return
    
    if message.channel.id != SUBMISSIONS_CHANNEL:
        await client.process_commands(message)
        return
    
    #Don't add DB entry for mods
    guild = message.guild
    if guild is None:
        return  

    member = guild.get_member(message.author.id)
    if member is None:
        return 

    if any(role.id == MODERATOR_ROLE for role in member.roles):
        await client.process_commands(message)
        return
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    
    for attachment in message.attachments:
        if attachment.filename.lower().endswith(image_extensions):
            isMedia = True

    if not isMedia:

        bot_deleted_messages.add(message.id)
        await message.delete()

        await message.channel.send("You are not allowed to send anything other than images here.", delete_after = 10)
        
        await client.process_commands(message)
        return
    
    if len(message.attachments) > 1:

        bot_deleted_messages.add(message.id)
        await message.delete()

        await message.channel.send("You are not allowed to send more than one submission.", delete_after = 10)

        await client.process_commands(message)
        return

    if user_exists(message.author.id):

        bot_deleted_messages.add(message.id)
        await message.delete()

        await message.channel.send("You have already posted your submission. If you want to change / edit your submission, delete your original submission and create a new one.", delete_after = 10)
        
        await client.process_commands(message)
        return
    
    await message.channel.send(f"{message.author.mention} your submission is successful. You **must delete** the submission if you want to change / edit your submission and post a new submission.", delete_after = 20)
    
    # create threads for each submission

    thread = await message.create_thread(
        name = f"{message.author.name}'s submission",
        auto_archive_duration = 10080
    )

    await thread.edit(slowmode_delay = 10) # 10 second slowmode

    await thread.send(f"Thread created for the discussion of {message.author.name}'s submission. Remember to keep the discussion respectful.")

    await client.process_commands(message)

    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (username, userid, messageid, threadid) VALUES (?, ?, ?, ?)',
            (str(message.author), message.author.id, message.id, thread.id))
    conn.commit()
    conn.close()

@client.event
async def on_message_delete(message):

    if message.id in bot_deleted_messages:
        bot_deleted_messages.remove(message.id)
        return
        
    isMedia = False
    
    if client.user == message.author:
        return
    
    if message.channel.id != SUBMISSIONS_CHANNEL:
        return
    
    #Don't add DB entry for mods
    guild = message.guild
    if guild is None:
        return  

    member = guild.get_member(message.author.id)
    if member is None:
        return 

    if any(role.id == MODERATOR_ROLE for role in member.roles):
        return
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    
    for attachment in message.attachments:
        if attachment.filename.lower().endswith(image_extensions):
            isMedia = True

    if isMedia:
        conn = sqlite3.connect('messages.db')
        c = conn.cursor()

        # delete the thread

        c.execute("SELECT threadid FROM messages WHERE messageid = ?", (message.id,))
        result = c.fetchone()

        thread_id = result[0]

        thread = await message.guild.fetch_channel(thread_id)
        await thread.delete()

        await message.channel.send(f"{message.author.mention} your submission was deleted and the thread has been removed. You are free to post a new submission if you would like.", delete_after = 10)

        c.execute('DELETE FROM messages WHERE messageid = ?', (message.id,))
        conn.commit()
        conn.close()

client.run(TOKEN)