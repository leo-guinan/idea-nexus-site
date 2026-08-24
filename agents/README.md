# INV Guide Agent

The public ElevenLabs Convai agent for Idea Nexus Ventures.

- Prompt source: `agents/inv-guide-prompt.md`
- Creation and readback script: `scripts/create_inv_agent.py`
- Receipt: `agents/inv-guide-receipt.json` (created after API verification)

The API key is read from `ELEVENLABS_API_KEY` or `~/.hermes/.env`. It is never written to the repository or printed.

The agent is public/anonymous for web use. The site should embed it only after the agent ID has been verified and the browser round-trip has been tested.
