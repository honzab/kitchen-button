__all__ = ["main"]


def main() -> None:
    # Imported lazily so that `playlist_button.config` stays importable on
    # machines without gpiozero/spotipy (e.g. for checking a config file).
    from .playlist_button import main as _main

    _main()
