import functools
import re
from collections.abc import Callable
from string import Template
from typing import Any, Final

import emoji
from discord import ApplicationContext, ClientUser, Color, Embed, File, Message, User
from discord.abc import GuildChannel
from discord.ui import View

_NO_COLOR: Final[int] = -1

_sanitize_channel_name: Final[Callable[[str], str]] = functools.partial(
    re.compile(r"(:[\w-]+:|^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$)", re.ASCII).sub, ""
)


def _pop_color(kwargs_dict: dict[str, Any]) -> Color | int:
    for key in ("color", "colour"):
        if key in kwargs_dict:
            return kwargs_dict.pop(key)
    return _NO_COLOR


def create_embed(description: str = "", *, title: str = "", **kwargs: Any) -> Embed:
    color = _pop_color(kwargs)
    return Embed(
        color=color if (color != _NO_COLOR) else Embed.Empty,
        title=title or Embed.Empty,
        description=description or Embed.Empty,
        **kwargs,
    )


def create_embed_for_author(
    user: ClientUser | User,
    description: str = "",
    *,
    header_template: str = "$user",
    header_link_url: str | None = None,
    **kwargs: Any,
) -> Embed:
    color = _pop_color(kwargs)

    if (color == _NO_COLOR) and user.color.value:
        color = user.color

    return create_embed(description, color=color, **kwargs).set_author(
        name=Template(header_template).substitute(user=user.display_name),
        url=header_link_url or Embed.Empty,
        icon_url=user.avatar.url,
    )


def create_embed_for_message(message: Message, /, *, link: bool = True) -> Embed:
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
) -> Embed:
    return create_embed(description, title=title, color=Color.brand_red())


async def edit_or_respond(
    ctx: ApplicationContext,
    *,
    content: str | None = None,
    embed: Embed | None = None,
    view: View | None = None,
) -> None:
    func = ctx.edit if ctx.response.is_done() else ctx.respond
    await func(content=content, embed=embed, view=view)


def get_asset_file(file_name: str) -> File:
    return File(f"taterbot/assets/{file_name}")


def get_channel_display_name(
    channel: GuildChannel,
    user: User | None,
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


def get_channel_loggable_name(channel: GuildChannel) -> str:
    return get_channel_display_name(
        channel, user=None, allow_mention=False, bold_text=False
    )


def get_color_value(color: str) -> int:
    color = re.sub(r"\W", "", color.lower(), re.ASCII)

    if color in ["", "default", "embed_background"]:
        return _NO_COLOR
    elif hasattr(Color, color):
        return getattr(Color, color).value
    else:
        return min(abs(int(color, 16)), 0xFFFFFF)


def get_embeds_from_message(message: Message, /) -> list[Embed]:
    embeds = []

    for sticker in message.stickers:
        sticker_embed = create_embed(
            title=f"{sticker.name} (Sticker)",
        ).set_image(url=sticker.url)
        embeds.append(sticker_embed)

    embeds.extend(message.embeds)
    return embeds


async def get_files_from_message(message: Message, /) -> list[File]:
    return [
        (await attachment.to_file(use_cached=True))
        for attachment in message.attachments
    ]
