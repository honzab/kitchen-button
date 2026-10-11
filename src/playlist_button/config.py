"""Configuration loading for the kitchen button.

All deployment-specific values (credentials, playlist, device, GPIO pin) live in
a TOML file so the code can be committed publicly. See config.example.toml.
"""

import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

CONFIG_ENV_VAR = "PLAYLIST_BUTTON_CONFIG"

#: Searched in order; the first existing file wins.
CONFIG_SEARCH_PATHS = (
    Path("config.toml"),
    Path("~/.config/kitchen-button/config.toml"),
    Path(__file__).resolve().parent.parent.parent / "config.toml",
)

DEFAULT_SCOPE = "user-read-playback-state user-modify-playback-state"


class ConfigError(Exception):
    """Raised when the config file is missing or incomplete."""


@dataclass(frozen=True)
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str = "http://127.0.0.1:8888/callback"
    cache_path: str = "~/.spotify_token"
    scope: str = DEFAULT_SCOPE


@dataclass(frozen=True)
class PlaybackConfig:
    device_name: str
    playlist_uri: str
    volume: int | None = None
    shuffle: bool = True


@dataclass(frozen=True)
class ButtonConfig:
    gpio_pin: int = 17
    toggle_switch: bool = False
    bounce_time: float = 0.05


@dataclass(frozen=True)
class Config:
    spotify: SpotifyConfig
    playback: PlaybackConfig
    button: ButtonConfig


def find_config_file() -> Path:
    override = os.environ.get(CONFIG_ENV_VAR)
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise ConfigError(
                f"{CONFIG_ENV_VAR} points at {path}, which does not exist"
            )
        return path

    for candidate in CONFIG_SEARCH_PATHS:
        path = candidate.expanduser()
        if path.is_file():
            return path

    searched = ", ".join(str(p) for p in CONFIG_SEARCH_PATHS)
    raise ConfigError(
        f"No config file found (searched: {searched}). "
        "Copy config.example.toml to config.toml and fill it in, "
        f"or set {CONFIG_ENV_VAR}."
    )


def _section(data: dict, name: str, path: Path) -> dict:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"[{name}] in {path} must be a table")
    return value


def _build(cls, values: dict, section: str, path: Path):
    known = set(cls.__dataclass_fields__)
    unknown = set(values) - known
    if unknown:
        raise ConfigError(
            f"Unknown key(s) in [{section}] of {path}: {', '.join(sorted(unknown))}"
        )
    try:
        return cls(**values)
    except TypeError as e:
        raise ConfigError(f"Invalid [{section}] in {path}: {e}") from e


def load_config(path: Path | None = None) -> Config:
    path = path or find_config_file()
    with path.open("rb") as f:
        data = tomllib.load(f)

    spotify = _section(data, "spotify", path)
    # Secrets may come from the environment instead of the file, which keeps
    # them out of config.toml entirely (e.g. systemd EnvironmentFile).
    for key, env_var in (
        ("client_id", "SPOTIFY_CLIENT_ID"),
        ("client_secret", "SPOTIFY_CLIENT_SECRET"),
    ):
        if env_var in os.environ:
            spotify[key] = os.environ[env_var]

    config = Config(
        spotify=_build(SpotifyConfig, spotify, "spotify", path),
        playback=_build(
            PlaybackConfig, _section(data, "playback", path), "playback", path
        ),
        button=_build(ButtonConfig, _section(data, "button", path), "button", path),
    )
    return replace(
        config,
        spotify=replace(
            config.spotify,
            cache_path=str(Path(config.spotify.cache_path).expanduser()),
        ),
    )
