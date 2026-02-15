# Vibe Sentinel Video Plan (Streamlined)

This file is operational prep only.  
Narration lives in `DEMO_SCRIPT.md`.

## Runtime target

- Length: 4:30 (safe inside 3-5 minute requirement)
- Resolution: 1920x1080
- FPS: 30
- Windows visible: terminal + browser only

## One-time setup

```bash
cd "/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Recording launch (fresh demo state)

```bash
cd "/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon"
source .venv/bin/activate
./scripts/run_video_demo.sh ./demo-repo-video 8765 --fresh
```

Use `--no-fresh` if you want to keep the repo state between retakes.

Then open: `http://127.0.0.1:8765`  
Project path to paste in Studio:  
`/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/demo-repo-video`

## Shot order (no narration text)

1. Hero + controls
2. Baseline `Run Audit`
3. `What-If Score Simulator` toggles
4. `Generate Agent Pack` and preview
5. `Launch Ship Sequence`
6. Milestone cards + celebration
7. `Run Coach` preview
8. `Start Demo Tour`
9. Final frame: score + timeline + artifacts

## Export checklist

- [ ] MP4 exported
- [ ] Title: `Vibe Sentinel - Agentic Shipping Console`
- [ ] Captions enabled
- [ ] Uploaded to YouTube or Loom
- [ ] Final URL pasted into `SUBMISSION.md`
