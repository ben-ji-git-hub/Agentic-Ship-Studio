# Beginner Tutorial (5 Minutes)

This guide matches the in-app tutorial in Studio.

## 1) Launch Studio

```bash
cd "/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon"
source .venv/bin/activate
vibe-sentinel studio --host 127.0.0.1 --port 8765
```

Open: `http://127.0.0.1:8765/index.html`

Optional first stop for a concise product walkthrough:
`http://127.0.0.1:8765/tutorial.html`

## 2) Set your project path

- Paste your repo path in `Project Path`.
- Example: `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/demo-repo-video`

## 3) Run baseline audit

- Click `Run Audit`.
- Read projected score, open findings, and top actions.

## 4) Run ship sequence

- Keep `Apply safe starter files` enabled.
- Click `Launch Ship Sequence`.
- This runs: audit -> agent-pack -> coach -> roadmap -> re-audit.

## 5) Read beginner fix guidance

- In the `Artifacts` list, open `coach_markdown`.
- Follow the action cards in order: high -> medium -> low.

## 6) Optional next steps

- Click `Show Advanced Actions` for `Agent Pack`, `Coach`, and `Roadmap` as standalone runs.
- Use `Start Demo Tour` for an automatic panel-by-panel walkthrough.

## Beginner shortcut

- Click `Start Beginner Tutorial` and then `Do Next Tutorial Step` repeatedly.
- Studio will guide and trigger the next action for you.
