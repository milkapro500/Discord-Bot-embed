## Research Summary for Cheet Master Assistant Discord Bot

### 1. Discord Embed Messages
- Discord Embeds are rich, formatted messages that can include a title, description, fields, images, and a color bar on the left side.
- The `discord.py` library is the standard for Python Discord bot development and provides robust support for creating and sending Embeds.
- The color bar can be set using `discord.Color` objects, which can be initialized from RGB values (e.g., `discord.Color.from_rgb(255,255,255)` for white).
- Embeds are a good way to present information cleanly and attractively.

### 2. Custom Emojis and Stickers
- Discord distinguishes between custom emojis and stickers. The user's request mentions "naklejki" (stickers) and "naklejek/emotek" (stickers/emotes), implying both.
- Custom emojis on Discord are typically formatted as `<:emoji_name:emoji_id>`. To use them, the bot needs to have access to the server where the emoji is available.
- The `discord.py` library allows bots to access server emojis. The `discord.Emoji` object can be converted to a string representation for use in messages.
- The challenge will be to parse user input (e.g., `:psc:`) and replace it with the correct Discord emoji format if the emoji exists on the server the bot is in.
- Stickers are a newer feature and might require different handling than custom emojis. I need to investigate how `discord.py` handles stickers specifically.

### 3. Discord Bot Development Best Practices
- Use `discord.py` (or `pycord`, a fork of `discord.py`) for Python bot development.
- Start with a simple bot and gradually add features.
- Consider bot sharding for larger bots, though likely not necessary for this initial project.
- Proper error handling and logging are crucial.

### Next Steps:
- Investigate `discord.py`'s specific support for Discord Stickers, as the search results primarily focused on custom emojis.
- Plan the bot's command structure for sending Embed messages.
- Design how the bot will parse user input for custom emojis/stickers and replace them with the correct format.



### 4. Discord Stickers and Emojis - Detailed Information

Based on the Discord.py documentation research:

#### Stickers:
- Discord has two types of stickers: `StandardSticker` (Discord's built-in stickers) and `GuildSticker` (custom server stickers)
- `GuildSticker` objects represent custom stickers created on a specific server
- Key properties of stickers:
  - `name`: The sticker's name
  - `id`: The sticker's unique ID
  - `description`: The sticker's description
  - `format`: The format type (PNG, APNG, Lottie, GIF)
  - `url`: The URL to access the sticker image
  - `guild`: The guild (server) the sticker belongs to (for GuildStickers)

#### Accessing Guild Stickers:
- `bot.get_sticker(sticker_id)`: Get a sticker by ID from the bot's cache
- `guild.stickers`: List of all stickers available in a guild
- `guild.fetch_stickers()`: Fetch all stickers from a guild (API call)

#### Emojis:
- Custom emojis are represented by `discord.Emoji` objects
- Format: `<:emoji_name:emoji_id>` for custom emojis
- `bot.get_emoji(emoji_id)`: Get an emoji by ID from the bot's cache
- `guild.emojis`: List of all custom emojis available in a guild

#### Implementation Strategy:
1. Parse user input for patterns like `:psc:` or `:blik:`
2. Search through the guild's stickers and emojis for matching names
3. Replace the text patterns with the appropriate Discord format
4. For stickers: Use the sticker object directly in the message
5. For emojis: Replace with `<:name:id>` format

#### Required Intents:
- `intents.emojis_and_stickers = True` is needed to access guild emojis and stickers

