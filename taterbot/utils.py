import functools
import re
from collections.abc import Callable
from string import Template
from typing import Any, Final

import emoji
from discord import Color, Embed, File, Message, User, abc

_sanitize_channel_name: Final[Callable[[str], str]] = functools.partial(
    re.compile(r"(:\w+:|^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$)").sub, ""
)


def create_embed(
    description: str = "",
    *,
    title: str = "",
    color: Color | int = 0xF09C96,
    **kwargs: Any,
) -> Embed:
    return Embed(
        color=color,
        title=title or Embed.Empty,
        description=description or Embed.Empty,
        **kwargs,
    )


def create_embed_for_author(
    user: abc.User,
    /,
    description: str = "",
    header_template: str = "$user",
    header_link_url: str | None = None,
    **kwargs: Any,
) -> Embed:
    return create_embed(description, **kwargs).set_author(
        name=Template(header_template).substitute(user=user.display_name),
        url=header_link_url or Embed.Empty,
        icon_url=user.avatar.url,
    )


def create_embed_for_message(message: Message, *, link: bool = True) -> Embed:
    return create_embed_for_author(
        message.author,
        description=message.content,
        header_template="Message from $user",
        header_link_url=message.jump_url if link else None,
        timestamp=message.created_at,
    )


def create_error_embed(
    description: str = "",
    *,
    title: str = "Something went wrong!",
    color: Color | int = Color.brand_red(),
) -> Embed:
    return create_embed(description, title=title, color=color)


def get_asset_file(file_name: str) -> File:
    return File(f"taterbot/assets/{file_name}")


def get_channel_display_name(
    channel: abc.GuildChannel,
    user: User | None = None,
    *,
    allow_mention: bool = True,
    bold_text: bool = True,
) -> str:
    if user and allow_mention:
        mutual_guild_ids = [guild.id for guild in user.mutual_guilds]
        if channel.guild.id in mutual_guild_ids:
            return channel.mention

    sanitized_name = _sanitize_channel_name(emoji.demojize(channel.name))
    display_name = f"#{sanitized_name}" if sanitized_name else f"Channel #{channel.id}"
    return f"**{display_name}**" if bold_text else display_name


def get_embeds_from_message(message: Message) -> list[Embed]:
    embeds = []

    for sticker in message.stickers:
        sticker_embed = create_embed(
            title=f"{sticker.name} (Sticker)",
        ).set_image(url=sticker.url)
        embeds.append(sticker_embed)

    embeds.extend(message.embeds)
    return embeds


async def get_files_from_message(message: Message) -> list[File]:
    return [
        (await attachment.to_file(use_cached=True))
        for attachment in message.attachments
    ]


def get_loggable_channel_name(channel: abc.GuildChannel) -> str:
    return get_channel_display_name(channel, allow_mention=False, bold_text=False)
