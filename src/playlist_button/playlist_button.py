#!/usr/bin/env python3
import logging
import sys
from signal import pause

import spotipy
from gpiozero import Button
from spotipy.oauth2 import SpotifyOAuth

from .config import Config, ConfigError, load_config


class Player:
    def __init__(self, config: Config):
        self.config = config
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config.spotify.client_id,
                client_secret=config.spotify.client_secret,
                redirect_uri=config.spotify.redirect_uri,
                scope=config.spotify.scope,
                open_browser=False,
                cache_path=config.spotify.cache_path,
            )
        )

    def find_device(self):
        name = self.config.playback.device_name
        for d in self.sp.devices()["devices"]:
            if d["name"].lower() == name.lower():
                return d["id"]
        logging.warning("Device '%s' not visible to Spotify (asleep/offline?)", name)
        return None

    def play(self):
        try:
            dev = self.find_device()
            if dev:
                playback = self.config.playback
                if playback.volume is not None:
                    self.sp.volume(playback.volume, device_id=dev)  # 0-100 percent
                self.sp.start_playback(device_id=dev, context_uri=playback.playlist_uri)
                if playback.shuffle:
                    self.sp.shuffle(True, device_id=dev)
                    self.sp.next_track(device_id=dev)
                logging.info("Started playlist on %s", playback.device_name)
        except Exception as e:
            logging.error("Play failed: %s", e)

    def pause_playback(self):
        try:
            self.sp.pause_playback()
            logging.info("Paused")
        except Exception as e:
            logging.error("Pause failed: %s", e)

    def toggle(self):
        try:
            state = self.sp.current_playback()
            if state and state.get("is_playing"):
                self.pause_playback()
            else:
                self.play()
        except Exception as e:
            logging.error("Toggle failed: %s", e)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    try:
        config = load_config()
    except ConfigError as e:
        logging.error("%s", e)
        sys.exit(1)

    player = Player(config)

    button = Button(
        config.button.gpio_pin,
        pull_up=True,
        bounce_time=config.button.bounce_time,
    )
    if config.button.toggle_switch:
        button.when_pressed = player.play  # contacts closed
        button.when_released = player.pause_playback
    else:
        button.when_pressed = player.toggle

    logging.info("Listening on GPIO%d", config.button.gpio_pin)
    pause()


if __name__ == "__main__":
    main()
