from flask import Flask, request, Response, abort
from flask_cors import CORS
import requests, urllib.parse

app = Flask(__name__)
# Allow any origin for demo; tighten in production
CORS(app, resources={r"/*": {"origins": "*"}})

ALLOWED_HOSTS = {
    "coastwatch.pfeg.noaa.gov",
    "oceanwatch.pfeg.noaa.gov",
}

def allowed(url: str) -> bool:
    try:
        u = urllib.parse.urlparse(url)
        return u.scheme in ("http", "https") and u.hostname in ALLOWED_HOSTS
    except Exception:
        return False

@app.route("/proxy")
def proxy():
    url = request.args.get("url", "")
    if not allowed(url):
        abort(400, "Blocked host")
    try:
        r = requests.get(url, stream=True, timeout=25)
        # Copy upstream headers but drop hop-by-hop
        headers = {k: v for k, v in r.headers.items()
                   if k.lower() not in ("content-encoding", "transfer-encoding", "connection")}
        # Explicit CORS headers for safety
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "*"
        return Response(r.iter_content(chunk_size=8192),
                        status=r.status_code,
                        headers=headers,
                        content_type=headers.get("Content-Type", "application/octet-stream"))
    except requests.RequestException as e:
        abort(502, f"Upstream error: {e}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)