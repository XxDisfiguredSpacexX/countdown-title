"""Rewrite the video title with the live view count and days left until 7 May 2027.

    python3 update_title.py VIDEO_ID            update the title if it changed
    python3 update_title.py VIDEO_ID --dry-run  show the new title, change nothing
    python3 update_title.py --test              check the title wording

Credentials come from env vars (GitHub Actions) or token.json (your Mac, made by login.py).
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

QUIT_DAY = date(2027, 5, 7)
TZ = ZoneInfo("Australia/Melbourne")  # days tick over at Melbourne midnight, same as the wallpaper
API = "https://www.googleapis.com/youtube/v3/videos"
# Fields we send back on update; anything left out of the snippet gets wiped by YouTube.
KEEP = ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage")


def build_title(views, days):
    who = "Nobody knows" if views == 0 else "1 person knows" if views == 1 else f"{views:,} people know"
    if days > 1:
        return f"{who} I'm quitting my job in {days} days"
    if days == 1:
        return f"{who} I'm quitting my job tomorrow"
    if days == 0:
        return f"{who} I'm quitting my job today"
    return f"{who} I quit my job"


def credentials():
    if os.environ.get("REFRESH_TOKEN"):
        return {k: os.environ[k] for k in ("CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN")}
    return json.loads((Path(__file__).parent / "token.json").read_text())


def access_token(creds):
    body = urllib.parse.urlencode({
        "client_id": creds["CLIENT_ID"],
        "client_secret": creds["CLIENT_SECRET"],
        "refresh_token": creds["REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", body))["access_token"]


def call(method, params, token, body=None):
    req = urllib.request.Request(
        f"{API}?{urllib.parse.urlencode(params)}",
        data=json.dumps(body).encode() if body else None,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req))


def main(video_id, dry_run):
    token = access_token(credentials())
    items = call("GET", {"part": "snippet,statistics", "id": video_id}, token)["items"]
    if not items:
        raise SystemExit(f"No video with ID {video_id} on this channel.")
    video = items[0]
    views = int(video["statistics"]["viewCount"])
    days = (QUIT_DAY - datetime.now(TZ).date()).days
    title = build_title(views, days)
    old = video["snippet"]["title"]

    if title == old:
        print(f"No change: {old}")
        return
    print(f"{old}\n  -> {title}")
    if dry_run:
        return
    snippet = {k: v for k, v in video["snippet"].items() if k in KEEP}
    snippet["title"] = title
    call("PUT", {"part": "snippet"}, token, {"id": video_id, "snippet": snippet})
    print("Updated.")


def test():
    assert build_title(0, 188) == "Nobody knows I'm quitting my job in 188 days"
    assert build_title(1, 188) == "1 person knows I'm quitting my job in 188 days"
    assert build_title(77319102, 2) == "77,319,102 people know I'm quitting my job in 2 days"
    assert build_title(5, 1) == "5 people know I'm quitting my job tomorrow"
    assert build_title(5, 0) == "5 people know I'm quitting my job today"
    assert build_title(5, -3) == "5 people know I quit my job"
    assert len(build_title(10**10, 10**4)) <= 100  # YouTube's title limit
    print("All title checks passed.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--test" in sys.argv:
        test()
    else:
        video_id = args[0] if args else os.environ.get("VIDEO_ID")
        if not video_id:
            raise SystemExit("Give the video ID: python3 update_title.py VIDEO_ID")
        main(video_id, "--dry-run" in sys.argv)
