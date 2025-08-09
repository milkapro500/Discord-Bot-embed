import discord
from discord.ext import commands
from discord import app_commands
import re
import os
import asyncio
from config import TOKEN
from settings_manager import SettingsManager

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.emojis_and_stickers = True

bot = commands.Bot(command_prefix="", intents=intents) # Changed prefix to empty for slash commands focus

# Initialize settings manager
settings_manager = SettingsManager()

@bot.event
async def on_ready():
    print(f'🤖 Cheet Master Assistant is online!')
    print(f'Bot Name: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Connected to {len(bot.guilds)} servers')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync slash commands: {e}')
    
    print('------')

# Helper functions
def get_color_from_string(color_input):
    """Convert color string to discord.Color object"""
    color_map = {
        'red': discord.Color.red(),
        'green': discord.Color.green(),
        'blue': discord.Color.blue(),
        'yellow': discord.Color.yellow(),
        'orange': discord.Color.orange(),
        'purple': discord.Color.purple(),
        'magenta': discord.Color.magenta(),
        'gold': discord.Color.gold(),
        'dark_red': discord.Color.dark_red(),
        'dark_green': discord.Color.dark_green(),
        'dark_blue': discord.Color.dark_blue(),
        'dark_purple': discord.Color.dark_purple(),
        'dark_magenta': discord.Color.dark_magenta(),
        'dark_gold': discord.Color.dark_gold(),
        'black': discord.Color.from_rgb(0, 0, 0),
        'white': discord.Color.from_rgb(255, 255, 255)
    }
    
    if color_input.lower() in color_map:
        return color_map[color_input.lower()]
    elif color_input.startswith('#') and len(color_input) == 7:
        try:
            hex_color = int(color_input[1:], 16)
            return discord.Color(hex_color)
        except ValueError:
            pass
    
    return discord.Color.blue()  # default

def parse_custom_emojis(content, guild):
    """Parse content for custom emoji patterns like :name:"""
    if not guild:
        return content
    
    pattern = r':([a-zA-Z0-9_]+):'
    matches = re.findall(pattern, content)
    
    for match in matches:
        for emoji in guild.emojis:
            if emoji.name.lower() == match.lower():
                content = content.replace(f':{match}:', str(emoji))
                break
    
    return content

def check_user_permissions(interaction: discord.Interaction) -> bool:
    """Check if user has permission to use bot commands"""
    if not interaction.guild:
        return True  # Allow in DMs
    
    # Get user's role IDs
    user_role_ids = [role.id for role in interaction.user.roles]
    
    # Check if user is allowed
    return settings_manager.is_user_allowed(interaction.guild.id, user_role_ids)

def check_admin_permissions(interaction: discord.Interaction) -> bool:
    """Check if user has admin permissions to manage bot settings"""
    if not interaction.guild:
        return False  # No admin in DMs
    
    # Check if user has manage roles or administrator permission
    return (interaction.user.guild_permissions.manage_roles or 
            interaction.user.guild_permissions.administrator)

# SLASH COMMANDS

@bot.tree.command(name="ping", description="Sprawdza opóźnienie bota")
async def slash_ping(interaction: discord.Interaction):
    """Slash command version of ping"""
    if not check_user_permissions(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania komend tego bota!", ephemeral=True)
        return
    
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

@bot.tree.command(name="help", description="Pokazuje pomoc dla bota")
async def slash_help(interaction: discord.Interaction):
    """Slash command version of help"""
    if not check_user_permissions(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania komend tego bota!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🤖 Cheet Master Assistant - Pomoc",
        description="Bot do wysyłania wiadomości Embed z obsługą serwerowych naklejek i emotek",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 Komendy slash:",
        value="`/ping` - Sprawdza opóźnienie bota\n"
              "`/help` - Pokazuje tę pomoc\n"
              "`/embed` - Tworzy wiadomość embed\n"
              "`/list_emojis` - Lista emotek serwera\n"
              "`/list_stickers` - Lista naklejek serwera\n"
              "`/clear` - Czyści wiadomości z kanału\n"
              "`/settings` - Zarządzanie uprawnieniami ról (tylko admin)",
        inline=False
    )
    
    embed.add_field(
        name="🎨 Dostępne kolory:",
        value="red, green, blue, yellow, orange, purple, magenta, gold, black, white\n"
              "dark_red, dark_green, dark_blue, dark_purple, dark_magenta, dark_gold\n"
              "Lub hex: #FF0000, #00FF00, itp.",
        inline=False
    )
    
    embed.add_field(
        name="😀 Emotki i naklejki:",
        value="Użyj `:nazwa:` w treści wiadomości (np. `:psc:`, `:blik:`)\n"
              "Bot automatycznie znajdzie i użyje emotek/naklejek z serwera",
        inline=False
    )
    
    embed.set_footer(text="Cheet Master Assistant v2.1 | Slash Commands + Role Permissions")
    await interaction.response.send_message(embed=embed)

# Settings command group
class SettingsGroup(app_commands.Group):
    """Settings command group for managing role permissions"""
    
    def __init__(self):
        super().__init__(name="settings", description="Zarządzanie ustawieniami bota")
    
    @app_commands.command(name="add_role", description="Dodaje rolę do listy dozwolonych ról")
    @app_commands.describe(role="Rola, która ma otrzymać dostęp do komend bota")
    async def add_role(self, interaction: discord.Interaction, role: discord.Role):
        """Add a role to the allowed roles list"""
        if not check_admin_permissions(interaction):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania ustawieniami bota! Wymagane: Zarządzanie rolami lub Administrator.", ephemeral=True)
            return
        
        if not interaction.guild:
            await interaction.response.send_message("❌ Ta komenda działa tylko na serwerach!", ephemeral=True)
            return
        
        success = settings_manager.add_allowed_role(interaction.guild.id, role.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Rola dodana",
                description=f"Rola {role.mention} została dodana do listy dozwolonych ról.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="⚠️ Rola już istnieje",
                description=f"Rola {role.mention} już znajduje się na liście dozwolonych ról.",
                color=discord.Color.orange()
            )
        
        embed.set_footer(
            text=f"Wykonane przez {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="remove_role", description="Usuwa rolę z listy dozwolonych ról")
    @app_commands.describe(role="Rola, która ma zostać usunięta z listy dozwolonych")
    async def remove_role(self, interaction: discord.Interaction, role: discord.Role):
        """Remove a role from the allowed roles list"""
        if not check_admin_permissions(interaction):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania ustawieniami bota! Wymagane: Zarządzanie rolami lub Administrator.", ephemeral=True)
            return
        
        if not interaction.guild:
            await interaction.response.send_message("❌ Ta komenda działa tylko na serwerach!", ephemeral=True)
            return
        
        success = settings_manager.remove_allowed_role(interaction.guild.id, role.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Rola usunięta",
                description=f"Rola {role.mention} została usunięta z listy dozwolonych ról.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Rola nie znaleziona",
                description=f"Rola {role.mention} nie znajduje się na liście dozwolonych ról.",
                color=discord.Color.red()
            )
        
        embed.set_footer(
            text=f"Wykonane przez {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="list_roles", description="Wyświetla listę dozwolonych ról")
    async def list_roles(self, interaction: discord.Interaction):
        """List all allowed roles for the current guild"""
        if not check_admin_permissions(interaction):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania ustawieniami bota! Wymagane: Zarządzanie rolami lub Administrator.", ephemeral=True)
            return
        
        if not interaction.guild:
            await interaction.response.send_message("❌ Ta komenda działa tylko na serwerach!", ephemeral=True)
            return
        
        allowed_role_ids = settings_manager.get_allowed_roles(interaction.guild.id)
        
        embed = discord.Embed(
            title="🔒 Dozwolone role",
            color=discord.Color.blue()
        )
        
        if not allowed_role_ids:
            embed.description = "**Brak ograniczeń** - wszyscy użytkownicy mogą używać komend bota.\n\nAby ograniczyć dostęp, użyj `/settings add_role <rola>`."
        else:
            role_mentions = []
            for role_id in allowed_role_ids:
                role = interaction.guild.get_role(role_id)
                if role:
                    role_mentions.append(role.mention)
                else:
                    role_mentions.append(f"<@&{role_id}> (rola usunięta)")
            
            embed.description = f"Tylko użytkownicy z następującymi rolami mogą używać komend bota:\n\n" + "\n".join(role_mentions)
        
        embed.set_footer(
            text=f"Serwer: {interaction.guild.name}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="reset", description="Resetuje ustawienia ról (usuwa wszystkie ograniczenia)")
    async def reset_roles(self, interaction: discord.Interaction):
        """Reset role settings for the current guild"""
        if not check_admin_permissions(interaction):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania ustawieniami bota! Wymagane: Zarządzanie rolami lub Administrator.", ephemeral=True)
            return
        
        if not interaction.guild:
            await interaction.response.send_message("❌ Ta komenda działa tylko na serwerach!", ephemeral=True)
            return
        
        success = settings_manager.clear_guild_settings(interaction.guild.id)
        
        embed = discord.Embed(
            title="🔄 Ustawienia zresetowane",
            description="Wszystkie ograniczenia ról zostały usunięte. Wszyscy użytkownicy mogą teraz używać komend bota.",
            color=discord.Color.green()
        )
        
        embed.set_footer(
            text=f"Wykonane przez {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        
        await interaction.response.send_message(embed=embed)

# Add the settings group to the bot
bot.tree.add_command(SettingsGroup())

@bot.tree.command(name="embed", description="Tworzy wiadomość embed z kolorowym paskiem")
@app_commands.describe(
    title="Tytuł embed",
    description="Opis embed (użyj \\n dla nowej linii)",
    color="Kolor paska bocznego (red, green, blue, hex, itp.)",
    channel="Kanał, na który zostanie wysłana wiadomość (domyślnie bieżący)",
    field1_name="Nazwa pierwszego pola (opcjonalne)",
    field1_value="Wartość pierwszego pola (opcjonalne)",
    field2_name="Nazwa drugiego pola (opcjonalne)",
    field2_value="Wartość drugiego pola (opcjonalne)",
    field3_name="Nazwa trzeciego pola (opcjonalne)",
    field3_value="Wartość trzeciego pola (opcjonalne)",
    signature="Czy wyświetlić podpis (Wysłane przez...)?",
    timestamp="Czy wyświetlić datę i czas?"
)
async def slash_embed(
    interaction: discord.Interaction,
    title: str,
    description: str = "",
    color: str = "blue",
    channel: discord.TextChannel = None,
    field1_name: str = None,
    field1_value: str = None,
    field2_name: str = None,
    field2_value: str = None,
    field3_name: str = None,
    field3_value: str = None,
    signature: bool = True,
    timestamp: bool = True
):
    """Create an embed message with custom color and fields"""
    if not check_user_permissions(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania komend tego bota!", ephemeral=True)
        return
    
    # Set target channel
    target_channel = channel if channel else interaction.channel
    
    if not isinstance(target_channel, discord.TextChannel):
        await interaction.response.send_message("❌ Wybrany kanał nie jest kanałem tekstowym!", ephemeral=True)
        return

    # Replace \n with actual newlines in description
    processed_description = description.replace("\\n", "\n")

    # Create embed
    embed_color = get_color_from_string(color)
    embed = discord.Embed(
        title=title,
        description=processed_description,
        color=embed_color
    )
    
    # Add fields if provided
    fields = [
        (field1_name, field1_value),
        (field2_name, field2_value),
        (field3_name, field3_value)
    ]
    
    for field_name, field_value in fields:
        if field_name and field_value:
            # Process fields for newlines
            processed_field_name = field_name.replace("\\n", "\n")
            processed_field_value = field_value.replace("\\n", "\n")

            embed.add_field(name=processed_field_name, value=processed_field_value, inline=True)
    
    # Add footer based on signature and timestamp options
    if signature or timestamp:
        footer_text = []
        if signature:
            footer_text.append(f"Wysłane przez {interaction.user.display_name}")
        
        embed.set_footer(
            text=" | ".join(footer_text),
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        if timestamp:
            embed.timestamp = discord.utils.utcnow()
    
    # Send initial response to interaction (can be ephemeral)
    await interaction.response.send_message(f"Wysyłam wiadomość embed na kanał {target_channel.mention}...", ephemeral=True)

    # Send the actual embed to the target channel
    await target_channel.send(embed=embed)

@bot.tree.command(name="list_emojis", description="Pokazuje listę dostępnych emotek na serwerze")
async def slash_list_emojis(interaction: discord.Interaction):
    """List all custom emojis available on the server"""
    if not check_user_permissions(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania komend tego bota!", ephemeral=True)
        return
    
    if not interaction.guild:
        await interaction.response.send_message("❌ Ta komenda działa tylko na serwerach!", ephemeral=True)
        return
    
    if not interaction.guild.emojis:
        await interaction.response.send_message("❌ Ten serwer nie ma żadnych niestandardowych emotek!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"Emotki serwera {interaction.guild.name}",
        description="Lista dostępnych niestandardowych emotek:",
        color=discord.Color.green()
    )
    
    emoji_list = []
    for emoji in interaction.guild.emojis:
        emoji_list.append(f"{emoji} `:{emoji.name}:`")
    
    # Split into chunks if too many emojis
    chunk_size = 20
    for i in range(0, len(emoji_list), chunk_size):
        chunk = emoji_list[i:i+chunk_size]
        embed.add_field(
            name=f"Emotki ({i+1}-{min(i+chunk_size, len(emoji_list))})",
            value="\n".join(chunk),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="list_stickers", description="Naklejki nie są już obsługiwane bezpośrednio w embedach. Użyj komendy /list_emojis dla emotek.")
async def slash_list_stickers(interaction: discord.Interaction):
    if not check_user_permissions(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania komend tego bota!", ephemeral=True)
        return
    
    await interaction.response.send_message("Naklejki nie są już obsługiwane bezpośrednio w embedach. Użyj komendy `/list_emojis` dla emotek.", ephemeral=True)

@bot.tree.command(name="clear", description="Czyści wiadomości z kanału")
@app_commands.describe(
    channel="Kanał, z którego mają zostać usunięte wiadomości",
    amount="Liczba wiadomości do usunięcia (1-100, domyślnie 10)"
)
async def slash_clear(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    amount: int = 10
):
    """Clear messages from a channel"""
    if not check_user_permissions(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania komend tego bota!", ephemeral=True)
        return
    
    # Check permissions
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania wiadomościami!", ephemeral=True)
        return
    
    # Check if bot has permissions
    bot_member = interaction.guild.get_member(bot.user.id)
    if not channel.permissions_for(bot_member).manage_messages:
        await interaction.response.send_message(f"❌ Bot nie ma uprawnień do zarządzania wiadomościami w kanale {channel.mention}!", ephemeral=True)
        return
    
    # Validate amount
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Liczba wiadomości musi być między 1 a 100!", ephemeral=True)
        return
    
    # Send initial response
    await interaction.response.send_message(f"🧹 Czyszczę {amount} wiadomości z kanału {channel.mention}...", ephemeral=True)
    
    try:
        # Delete messages
        deleted = await channel.purge(limit=amount)
        
        # Send confirmation
        embed = discord.Embed(
            title="🧹 Wiadomości usunięte",
            description=f"Usunięto **{len(deleted)}** wiadomości z kanału {channel.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(
            text=f"Wykonane przez {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.timestamp = discord.utils.utcnow()
        
        # Send confirmation to the channel where command was used
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot nie ma uprawnień do usuwania wiadomości w tym kanale!", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ Wystąpił błąd podczas usuwania wiadomości: {e}", ephemeral=True)

# LEGACY PREFIX COMMANDS (for backward compatibility)

@bot.command(name='ping')
async def ping(ctx):
    """Test command to check if bot is responsive"""
    await ctx.send(f'🏓 Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.command(name='help_embed')
async def help_embed(ctx):
    """Show help for embed commands"""
    embed = discord.Embed(
        title="🤖 Cheet Master Assistant - Pomoc",
        description="Bot do wysyłania wiadomości Embed z obsługą serwerowych naklejek i emotek",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 Komendy slash (zalecane):",
        value="`/ping` - Sprawdza opóźnienie bota\n"
              "`/help` - Pokazuje pomoc\n"
              "`/embed` - Tworzy wiadomość embed\n"
              "`/list_emojis` - Lista emotek serwera\n"
              "`/list_stickers` - Lista naklejek serwera",
        inline=False
    )
    
    embed.add_field(
        name="📝 Stare komendy (nadal działają):",
        value="`!ping` - Sprawdza opóźnienie bota\n"
              "`!help_embed` - Pokazuje tę pomoc\n"
              "`!embed` - Podstawowy embed\n"
              "`!embed_with_stickers` - Embed z emotkami/naklejkami",
        inline=False
    )
    
    embed.add_field(
        name="🎨 Dostępne kolory:",
        value="red, green, blue, yellow, orange, purple, magenta, gold, black, white\n"
              "dark_red, dark_green, dark_blue, dark_purple, dark_magenta, dark_gold\n"
              "Lub hex: #FF0000, #00FF00, itp.",
        inline=False
    )
    
    embed.set_footer(text="Cheet Master Assistant v2.1 | Slash Commands + Role Permissions")
    await ctx.send(embed=embed)

@bot.command(name='embed')
async def send_embed(ctx, *, content=None):
    """Legacy embed command"""
    if not content:
        await ctx.send("❌ Podaj treść dla embed! Użyj: `!embed [tytuł] | [opis] | [kolor] | [pola]`\n"
                      "💡 **Tip:** Użyj nowej komendy `/embed` dla lepszego doświadczenia!")
        return
    
    # Parse the content
    parts = content.split('|')
    
    # Default values
    title = "Cheet Master Assistant"
    description = ""
    color = discord.Color.blue()
    fields = []
    
    # Parse title
    if len(parts) >= 1 and parts[0].strip():
        title = parts[0].strip()
    
    # Parse description
    if len(parts) >= 2 and parts[1].strip():
        description = parts[1].strip()
    
    # Parse color
    if len(parts) >= 3 and parts[2].strip():
        color = get_color_from_string(parts[2].strip())
    
    # Parse fields
    if len(parts) >= 4 and parts[3].strip():
        field_pairs = parts[3].strip().split(',')
        for pair in field_pairs:
            if ':' in pair:
                field_name, field_value = pair.split(':', 1)
                fields.append((field_name.strip(), field_value.strip()))
    
    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    # Add fields
    for field_name, field_value in fields:
        embed.add_field(name=field_name, value=field_value, inline=True)
    
    # Add footer
    embed.set_footer(text=f"Wysłane przez {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.timestamp = discord.utils.utcnow()
    
    await ctx.send(embed=embed)

@bot.command(name='embed_with_stickers')
async def send_embed_with_stickers(ctx, *, content=None):
    """Legacy embed command with stickers support"""
    if not content:
        await ctx.send("❌ Podaj treść dla embed! Użyj: `!embed_with_stickers [tytuł] | [opis] | [kolor] | [pola]`\n"
                      "💡 **Tip:** Użyj nowej komendy `/embed` dla lepszego doświadczenia!")
        return
    
    # Parse the content for custom emojis and stickers
    parsed_content = parse_custom_emojis(content, ctx.guild)
    
    # Parse the embed content (same as regular embed command)
    parts = parsed_content.split('|')
    
    # Default values
    title = "Cheet Master Assistant"
    description = ""
    color = discord.Color.blue()
    fields = []
    
    # Parse title
    if len(parts) >= 1 and parts[0].strip():
        title = parts[0].strip()
    
    # Parse description
    if len(parts) >= 2 and parts[1].strip():
        description = parts[1].strip()
    
    # Parse color
    if len(parts) >= 3 and parts[2].strip():
        color = get_color_from_string(parts[2].strip())
    
    # Parse fields
    if len(parts) >= 4 and parts[3].strip():
        field_pairs = parts[3].strip().split(',')
        for pair in field_pairs:
            if ':' in pair:
                field_name, field_value = pair.split(':', 1)
                fields.append((field_name.strip(), field_value.strip()))
    
    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    # Add fields
    for field_name, field_value in fields:
        embed.add_field(name=field_name, value=field_value, inline=True)
    
    # Add footer
    embed.set_footer(text=f"Wysłane przez {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.timestamp = discord.utils.utcnow()
    
    # Send embed
    await ctx.send(embed=embed)

@bot.command(name='list_emojis')
async def list_server_emojis(ctx):
    """Legacy command to list server emojis"""
    await ctx.send("💡 **Tip:** Użyj nowej komendy `/list_emojis` dla lepszego doświadczenia!")
    
    if not ctx.guild:
        await ctx.send("❌ Ta komenda działa tylko na serwerach!")
        return
    
    if not ctx.guild.emojis:
        await ctx.send("❌ Ten serwer nie ma żadnych niestandardowych emotek!")
        return
    
    embed = discord.Embed(
        title=f"Emotki serwera {ctx.guild.name}",
        description="Lista dostępnych niestandardowych emotek:",
        color=discord.Color.green()
    )
    
    emoji_list = []
    for emoji in ctx.guild.emojis:
        emoji_list.append(f"{emoji} `:{emoji.name}:`")
    
    # Split into chunks if too many emojis
    chunk_size = 20
    for i in range(0, len(emoji_list), chunk_size):
        chunk = emoji_list[i:i+chunk_size]
        embed.add_field(
            name=f"Emotki ({i+1}-{min(i+chunk_size, len(emoji_list))})",
            value="\n".join(chunk),
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='list_stickers')
async def list_server_stickers(ctx):
    """Legacy command to list server stickers"""
    await ctx.send("💡 **Tip:** Użyj nowej komendy `/list_stickers` dla lepszego doświadczenia!")
    
    if not ctx.guild:
        await ctx.send("❌ Ta komenda działa tylko na serwerach!")
        return
    
    if not ctx.guild.stickers:
        await ctx.send("❌ Ten serwer nie ma żadnych niestandardowych naklejek!")
        return
    
    embed = discord.Embed(
        title=f"Naklejki serwera {ctx.guild.name}",
        description="Lista dostępnych niestandardowych naklejek:",
        color=discord.Color.purple()
    )
    
    sticker_list = []
    for sticker in ctx.guild.stickers:
        sticker_list.append(f"`:{sticker.name}:` - {sticker.description or 'Brak opisu'}")
    
    # Split into chunks if too many stickers
    chunk_size = 15
    for i in range(0, len(sticker_list), chunk_size):
        chunk = sticker_list[i:i+chunk_size]
        embed.add_field(
            name=f"Naklejki ({i+1}-{min(i+chunk_size, len(sticker_list))})",
            value="\n".join(chunk),
            inline=False
        )
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if TOKEN == 'YOUR_BOT_TOKEN': # This line is incorrect, should be from config.py
        print("❌ Błąd: Ustaw token bota w pliku config.py")
    else:
        bot.run(TOKEN)

