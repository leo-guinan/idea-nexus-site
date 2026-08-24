#!/usr/bin/env python3
"""Create and verify the public ElevenLabs INV Guide agent without printing secrets."""
from pathlib import Path
import json, os, sys, urllib.request

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.elevenlabs.io/v1"
VOICE_ID = "xTJZGk1pM8cWu7HMnf9y"

def load_key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    env = Path.home()/".hermes"/".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ELEVENLABS_API_KEY not found in environment or ~/.hermes/.env")

def request(method, path, key, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API+path, data=data, method=method, headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:1000]
        raise SystemExit(f"ElevenLabs API {exc.code} on {method} {path}: {detail}")

def main():
    key = load_key()
    prompt = (ROOT/"agents/inv-guide-prompt.md").read_text()
    config = {
        "name": "INV Guide — Marvin",
        "conversation_config": {
            "agent": {
                "first_message": "Hi, I’m Marvin — the AI guide to Idea Nexus Ventures. I can explain the work, the AI audit, HumAIn products, or the research. I’m not a human, and I won’t invent an answer just to make the conversation feel complete. What would you like to understand?",
                "language": "en",
                "prompt": {"prompt": prompt, "llm": "gemini-2.5-flash", "temperature": 0.55}
            },
            "tts": {"voice_id": VOICE_ID, "model_id": "eleven_flash_v2", "stability": 0.5, "similarity_boost": 0.8},
            "asr": {"quality": "high"}
        }
    }
    status, created = request("POST", "/convai/agents/create", key, config)
    agent_id = created.get("agent_id")
    if not agent_id:
        raise SystemExit(f"Create returned {status} without agent_id")
    vstatus, verified = request("GET", f"/convai/agents/{agent_id}", key)
    auth = verified.get("platform_settings", {}).get("auth", {}).get("enable_auth")
    agent_cfg = verified.get("conversation_config", {}).get("agent", {})
    prompt_cfg = agent_cfg.get("prompt", {})
    tts_cfg = verified.get("conversation_config", {}).get("tts", {})
    if auth is True:
        raise SystemExit("Agent was created private; refusing to publish an unexpectedly private agent")
    if tts_cfg.get("voice_id") != VOICE_ID:
        raise SystemExit("Voice readback mismatch")
    if agent_cfg.get("first_message") != config["conversation_config"]["agent"]["first_message"]:
        raise SystemExit("First-message readback mismatch")
    link_status, link = request("POST", f"/convai/agents/{agent_id}/link", key, {"purpose": "shareable_link"})
    token = link.get("token", {}).get("conversation_token")
    (ROOT/"agents/inv-guide-receipt.json").write_text(json.dumps({
        "agent_id": agent_id,
        "name": verified.get("name", config["name"]),
        "public": auth is not True,
        "voice_id": tts_cfg.get("voice_id"),
        "llm": prompt_cfg.get("llm"),
        "temperature": prompt_cfg.get("temperature"),
        "prompt_characters": len(prompt_cfg.get("prompt", "")),
        "asr_quality": verified.get("conversation_config", {}).get("asr", {}).get("quality"),
        "shareable_link_token_created": bool(token),
        "verified_statuses": {"create": status, "agent_readback": vstatus, "link": link_status}
    }, indent=2)+"\n")
    print(json.dumps({"agent_id": agent_id, "public": auth is not True, "voice_id": tts_cfg.get("voice_id"), "llm": prompt_cfg.get("llm"), "temperature": prompt_cfg.get("temperature"), "prompt_characters": len(prompt_cfg.get("prompt", "")), "shareable_link_created": bool(token)}, indent=2))

if __name__ == "__main__":
    main()
