from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteButtonDescription:
    command: str
    name: str


REMOTE_BUTTONS = (
    RemoteButtonDescription("channel_up", "Channel up"),
    RemoteButtonDescription("channel_down", "Channel down"),
    RemoteButtonDescription("menu", "Menu"),
    RemoteButtonDescription("q_menu", "Quick menu"),
    RemoteButtonDescription("up", "Up"),
    RemoteButtonDescription("down", "Down"),
    RemoteButtonDescription("left", "Left"),
    RemoteButtonDescription("right", "Right"),
    RemoteButtonDescription("ok", "OK"),
    RemoteButtonDescription("back", "Back"),
    RemoteButtonDescription("exit", "Exit"),
    RemoteButtonDescription("guide", "Guide"),
    RemoteButtonDescription("home", "Home"),
    RemoteButtonDescription("netflix", "Netflix"),
    RemoteButtonDescription("prime_video", "Prime Video"),
    RemoteButtonDescription("youtube", "YouTube"),
    RemoteButtonDescription("red", "Red"),
    RemoteButtonDescription("green", "Green"),
    RemoteButtonDescription("yellow", "Yellow"),
    RemoteButtonDescription("blue", "Blue"),
    RemoteButtonDescription("info", "Info"),
    RemoteButtonDescription("list", "List"),
)

FAN_BUTTONS = (
    RemoteButtonDescription("mute", "Mute"),
    RemoteButtonDescription("speed", "Speed"),
)
