"""A small, dependency-free AI debate partner."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pathlib import Path
import json
import os

ROOT = Path(__file__).parent
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

SYSTEM = """You are a sharp, fair, curious debate partner and coach. Debate the user's stated side from the opposing position. Be rigorous without being hostile. Address their actual latest claim, identify assumptions or missing evidence, and offer one clear counterargument followed by one focused question. Never invent studies, statistics, quotations, or citations. Say when a claim needs evidence. Keep replies under 150 words. If asked to score, judge only the user's arguments in the supplied transcript on four equally weighted dimensions (0-10): claim clarity, evidence, reasoning, and engagement with counterarguments. Return valid JSON only, shaped as {"reply":"...","scores":{"clarity":0,"evidence":0,"reasoning":0,"engagement":0},"feedback":"..."}. For ordinary debate turns, use the same JSON shape; scores may be null and feedback a short coaching note."""

def local_reply(topic, side, message, history):
    """Useful offline starter, clearly disclosed in the interface."""
    msg = message.strip()
    low = msg.lower()
    if len(msg.split()) < 5:
        return (f"I hear your position, but I need the reasoning behind it. On **{topic}**, what is the strongest evidence or principle that supports your view?", "Try stating a specific claim, then give a reason or example that would let someone evaluate it.")
    if any(x in low for x in ("because", "evidence", "study", "data", "example", "would", "should", "may", "will")):
        return (f"That gives us a point to examine. One possible counter is that the case for **{side}** depends on whether the benefit you describe is large enough to outweigh the costs, trade-offs, and people affected differently. What evidence would distinguish a lasting effect from a short-term or selective example?", "You made a claim and offered a reason. Strengthen it by naming a source, explaining how it supports the claim, and addressing who might be an exception.")
    return (f"I can see the intuition behind that. A skeptic might ask whether the same reasoning holds across different contexts, and what unintended consequence could follow. For **{topic}**, how would you answer someone who agrees with your goal but thinks your proposed position is not the best way to reach it?", "Make the link between your point and the debate question explicit, then anticipate the strongest reasonable objection.")

def ask_model(payload):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    body = {"model": model, "temperature": 0.7, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
    req = Request(base + "/chat/completions", data=json.dumps(body).encode(),
                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=60) as res:
        data = json.loads(res.read())
    return json.loads(data["choices"][0]["message"]["content"])

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, status=200):
        raw = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw))); self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers(); self.wfile.write(raw)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS"); self.end_headers()
    def do_GET(self):
        if self.path == "/api/status":
            self.send_json({"mode": "ai" if os.getenv("OPENAI_API_KEY", "").strip() else "local", "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")}); return
        if self.path in ("/", "/index.html"):
            raw = (ROOT / "index.html").read_bytes(); self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        self.send_error(404)
    def do_POST(self):
        if self.path != "/api/debate": self.send_error(404); return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            topic = str(data.get("topic", ""))[:300]; side = str(data.get("side", ""))[:80]
            message = str(data.get("message", ""))[:4000]; history = data.get("history", [])[-24:]
            if not topic or not message: self.send_json({"error": "Add a debate question and an argument first."}, 400); return
            try:
                result = ask_model({"task": data.get("task", "debate"), "topic": topic, "user_side": side,
                                    "message": message, "transcript": history})
                if not isinstance(result, dict) or not result.get("reply"): raise ValueError("The model returned an incomplete response.")
                result["mode"] = "ai"
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
                reply, feedback = local_reply(topic, side, message, history)
                result = {"reply": reply, "feedback": feedback, "scores": None, "mode": "local",
                          "notice": "AI connection unavailable; using the local demo partner."}
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": "Could not process this turn. Please try again."}, 500)
    def log_message(self, fmt, *args): pass

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Debate partner ready at http://{HOST}:{PORT}")
    print("AI mode: " + (os.getenv("OPENAI_MODEL", "gpt-4o-mini") if os.getenv("OPENAI_API_KEY") else "local demo (set OPENAI_API_KEY for AI)"))
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nServer stopped."); server.server_close()
