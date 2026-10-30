"""One-off: sign in to your YouTube channel and get a refresh token.

Put the client_secret*.json you downloaded from Google Cloud next to this file, then:
    python3 login.py
Approve in the browser. It saves token.json and prints the three GitHub secrets.
"""
import json
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).parent
PORT = 8765
REDIRECT = f"http://127.0.0.1:{PORT}"
SCOPE = "https://www.googleapis.com/auth/youtube"

secret_files = sorted(HERE.glob("client_secret*.json"))
if not secret_files:
    raise SystemExit("No client_secret*.json here. Download it from Google Cloud > Credentials first.")
secret = json.loads(secret_files[0].read_text())["installed"]

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": secret["client_id"],
    "redirect_uri": REDIRECT,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",  # forces Google to hand back a refresh token
})

code = None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global code
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Done. You can close this tab and go back to Terminal." if code else b"No code - check Terminal.")

    def log_message(self, *args):
        pass


print("Opening your browser to sign in...")
webbrowser.open(auth_url)
server = HTTPServer(("127.0.0.1", PORT), Handler)
while code is None:
    server.handle_request()

body = urllib.parse.urlencode({
    "code": code,
    "client_id": secret["client_id"],
    "client_secret": secret["client_secret"],
    "redirect_uri": REDIRECT,
    "grant_type": "authorization_code",
}).encode()
tokens = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", body))
if "refresh_token" not in tokens:
    raise SystemExit(f"Google didn't return a refresh token: {tokens}")

creds = {
    "CLIENT_ID": secret["client_id"],
    "CLIENT_SECRET": secret["client_secret"],
    "REFRESH_TOKEN": tokens["refresh_token"],
}
(HERE / "token.json").write_text(json.dumps(creds, indent=2))
print("\nSaved token.json. Add these as GitHub repository secrets (Settings > Secrets and variables > Actions):\n")
for name, value in creds.items():
    print(f"{name}\n{value}\n")
