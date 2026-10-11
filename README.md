# KitchenButton Raspberry Pi Zero W

## `playlist_button.py`

### Installation

Kitchen switch -> Spotify Connect playlist.

Wiring: switch between GPIO17 (physical pin 11) and GND (physical pin 9).
No external voltage on the switch - the Pi's internal pull-up does the work.

```bash
sudo apt install python3-gpiozero python3-pip
pip install spotipy --break-system-packages
```

The script is a package now (it imports its config module), so install it
rather than copying the single file:

```bash
pip install . --break-system-packages
```

### Configuration

All deployment-specific values live in `config.toml`, which is gitignored:

```bash
cp config.example.toml config.toml
```

Create an app at https://developer.spotify.com/dashboard with redirect URI
`http://127.0.0.1:8888/callback`, then fill in `client_id`, `client_secret`,
`device_name` and `playlist_uri`.

The config file is looked up in this order, first hit wins:

1. `$PLAYLIST_BUTTON_CONFIG`
2. `./config.toml` (relative to the working directory)
3. `~/.config/kitchen-button/config.toml`
4. `config.toml` next to the repo root

`SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` override the file, so the
secrets can be kept out of `config.toml` entirely via a systemd
`EnvironmentFile=`.

Run the script once by hand to log in (see notes); after that it runs unattended.

### Notes

```
journalctl -u kitchen-switch -f
```

```
sudo systemctl daemon-reload
```

```
sudo systemctl restart kitchen-switch
```


`/etc/systemd/system/kitchen-switch.service`

```
[Service]
ExecStart=/usr/bin/python -m playlist_button
Environment=PLAYLIST_BUTTON_CONFIG=/home/kitchenbutton/config.toml
Restart=always
User=kitchenbutton
WorkingDirectory=/home/kitchenbutton
[Install]
WantedBy=multi-user.target
```
