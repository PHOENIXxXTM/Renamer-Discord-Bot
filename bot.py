import discord
from discord.ext import commands
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
@commands.has_permissions(administrator=True)
async def add_prefix(ctx, prefix: str):
    """Add a prefix to all members' display names in this server"""
    guild = ctx.guild
    
    # Add a space after the prefix
    formatted_prefix = f"{prefix} "
    
    # Confirmation message
    confirm_msg = await ctx.send(
        f"⚠️ This will add '{formatted_prefix}' to members who don't already have it. "
        f"Type 'confirm' to proceed or 'cancel' to abort."
    )
    
    # Wait for confirmation
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['confirm', 'cancel']
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await confirm_msg.edit(content="❌ Operation timed out. Please try again.")
        return
    
    if msg.content.lower() == 'cancel':
        await confirm_msg.edit(content="❌ Operation cancelled.")
        return
    
    # Proceed with name changes
    await confirm_msg.edit(content="🔄 Starting name changes... This may take a while.")
    
    changed = 0
    failed = 0
    skipped = 0
    
    for member in guild.members:
        # Skip bots if desired
        if member.bot:
            continue
            
        # Check if the name already has the prefix with space
        if member.display_name.startswith(formatted_prefix):
            skipped += 1
            continue
            
        # Check if the name already has the prefix without space followed by non-alphanumeric
        # This handles cases like "[VIP]Username" where there's no space but it's still a prefix
        if member.display_name.startswith(prefix) and len(member.display_name) > len(prefix):
            next_char = member.display_name[len(prefix)]
            if not next_char.isalnum():  # If it's a space, punctuation, etc.
                skipped += 1
                continue
        
        new_nickname = f"{formatted_prefix}{member.display_name}"
        
        # Discord has a 32-character limit for nicknames
        if len(new_nickname) > 32:
            # Calculate available space for the name (prefix + space = len(prefix)+1)
            available_length = 32 - (len(prefix) + 1)
            if available_length > 0:
                new_nickname = f"{formatted_prefix}{member.display_name[:available_length]}"
            else:
                # Prefix is too long, skip this user
                failed += 1
                continue
        
        try:
            await member.edit(nick=new_nickname)
            changed += 1
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            print(f"Missing permissions to change {member.name}'s nickname")
            failed += 1
        except discord.HTTPException:
            print(f"Failed to change {member.name}'s nickname")
            failed += 1
    
    await confirm_msg.edit(
        content=f"✅ Name change completed!\n"
                f"Changed: {changed} members\n"
                f"Skipped: {skipped} members (already had prefix)\n"
                f"Failed: {failed} members\n"
                f"Note: Some members might not have been changed due to permission issues or name length limits."
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_prefix(ctx, prefix: str):
    """Remove a specific prefix from all members' display names"""
    guild = ctx.guild
    formatted_prefix = f"{prefix} "
    
    confirm_msg = await ctx.send(
        f"⚠️ This will remove the prefix '{formatted_prefix}' from all member names. "
        f"Type 'confirm' to proceed or 'cancel' to abort."
    )
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['confirm', 'cancel']
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await confirm_msg.edit(content="❌ Operation timed out. Please try again.")
        return
    
    if msg.content.lower() == 'cancel':
        await confirm_msg.edit(content="❌ Operation cancelled.")
        return
    
    await confirm_msg.edit(content="🔄 Removing prefixes... This may take a while.")
    
    changed = 0
    failed = 0
    skipped = 0
    
    for member in guild.members:
        if member.bot:
            continue
            
        current_name = member.display_name
        
        # Check if the name starts with the prefix (with space)
        if current_name.startswith(formatted_prefix):
            # Remove prefix with space
            new_nickname = current_name[len(formatted_prefix):]
        # Check if the name starts with the prefix (without space but followed by non-alphanumeric)
        elif current_name.startswith(prefix) and len(current_name) > len(prefix):
            next_char = current_name[len(prefix)]
            if not next_char.isalnum():  # If it's a space, punctuation, etc.
                # Remove prefix and the following non-alphanumeric character
                new_nickname = current_name[len(prefix)+1:]
            else:
                skipped += 1
                continue
        else:
            skipped += 1
            continue
            
        # If after removal the name is empty, use their regular username
        if not new_nickname.strip():
            new_nickname = member.name
            
        try:
            await member.edit(nick=new_nickname)
            changed += 1
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            print(f"Missing permissions to change {member.name}'s nickname")
            failed += 1
        except discord.HTTPException:
            print(f"Failed to change {member.name}'s nickname")
            failed += 1
    
    await confirm_msg.edit(
        content=f"✅ Prefix removal completed!\n"
                f"Changed: {changed} members\n"
                f"Skipped: {skipped} members (didn't have the prefix)\n"
                f"Failed: {failed} members"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def check_prefix(ctx, prefix: str):
    """Check how many members already have a specific prefix"""
    guild = ctx.guild
    formatted_prefix = f"{prefix} "
    
    has_prefix = 0
    no_prefix = 0
    
    for member in guild.members:
        if member.bot:
            continue
            
        # Check if the name already has the prefix with space
        if member.display_name.startswith(formatted_prefix):
            has_prefix += 1
            continue
            
        # Check if the name already has the prefix without space followed by non-alphanumeric
        if member.display_name.startswith(prefix) and len(member.display_name) > len(prefix):
            next_char = member.display_name[len(prefix)]
            if not next_char.isalnum():  # If it's a space, punctuation, etc.
                has_prefix += 1
                continue
                
        no_prefix += 1
    
    await ctx.send(
        f"📊 Prefix status for '{prefix}':\n"
        f"Members with prefix: {has_prefix}\n"
        f"Members without prefix: {no_prefix}\n"
        f"Use `!add_prefix {prefix}` to add the prefix to members who don't have it."
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_all_nicknames(ctx):
    """Remove all nicknames from all members (reset to default username)"""
    guild = ctx.guild
    
    # Confirmation message
    confirm_msg = await ctx.send(
        "⚠️ **WARNING:** This will remove ALL nicknames from ALL members and reset them to their default usernames. "
        "This action cannot be undone. Type 'CONFIRM' to proceed or 'cancel' to abort."
    )
    
    # Wait for confirmation
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['confirm', 'cancel']
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await confirm_msg.edit(content="❌ Operation timed out. Please try again.")
        return
    
    if msg.content.lower() == 'cancel':
        await confirm_msg.edit(content="❌ Operation cancelled.")
        return
    
    await confirm_msg.edit(content="🔄 Removing all nicknames... This may take a while.")
    
    changed = 0
    failed = 0
    skipped = 0
    
    for member in guild.members:
        if member.bot:
            continue
            
        # Skip members who don't have a nickname (their display_name equals their username)
        if member.display_name == member.name:
            skipped += 1
            continue
        
        try:
            # Set nickname to None to remove it
            await member.edit(nick=None)
            changed += 1
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            print(f"Missing permissions to remove {member.name}'s nickname")
            failed += 1
        except discord.HTTPException:
            print(f"Failed to remove {member.name}'s nickname")
            failed += 1
    
    await confirm_msg.edit(
        content=f"✅ All nicknames removed!\n"
                f"Nicknames removed: {changed} members\n"
                f"Skipped: {skipped} members (already had no nickname)\n"
                f"Failed: {failed} members\n"
                f"Note: Some members might not have been changed due to permission issues."
    )

# Run the bot
if __name__ == "__main__":
    # Replace with your bot token
    bot.run('BOT-TOKEN')