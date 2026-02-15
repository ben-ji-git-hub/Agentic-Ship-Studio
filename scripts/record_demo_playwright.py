#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


def wait_for_http(url: str, timeout_seconds: float = 25.0) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout_seconds:
        try:
            with urlopen(url, timeout=1.5) as response:
                if 200 <= response.status < 500:
                    return
        except URLError:
            pass
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for server at {url}")


def scroll_smooth(page, amount: int, steps: int, delay_ms: int) -> None:
    if steps <= 0:
        return
    each = amount / steps
    for _ in range(steps):
        page.mouse.wheel(0, each)
        page.wait_for_timeout(delay_ms)


def wait_until_mark(page, start_time: float, mark_seconds: float) -> None:
    elapsed = time.monotonic() - start_time
    remaining = mark_seconds - elapsed
    if remaining > 0:
        page.wait_for_timeout(int(remaining * 1000))


def safe_click(page, selector: str, timeout_ms: int = 8_000) -> None:
    page.locator(selector).first.click(timeout=timeout_ms)


def clear_and_type(page, selector: str, value: str, delay_ms: int = 85) -> None:
    field = page.locator(selector).first
    field.click(timeout=8_000)
    for combo in ("Meta+A", "Control+A"):
        try:
            page.keyboard.press(combo)
        except Exception:
            pass
    page.keyboard.press("Backspace")
    page.keyboard.type(value, delay=delay_ms)
    page.wait_for_timeout(500)


def run_walkthrough(base_url: str, project_path: str, out_video_path: Path) -> None:
    out_video_path.parent.mkdir(parents=True, exist_ok=True)
    temp_video_dir = out_video_path.parent / "pw_tmp_video"
    if temp_video_dir.exists():
        shutil.rmtree(temp_video_dir)
    temp_video_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            record_video_dir=str(temp_video_dir),
            record_video_size={"width": 1600, "height": 900},
        )
        page = context.new_page()
        start = time.monotonic()

        page.goto(f"{base_url}/tutorial.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2_500)
        scroll_smooth(page, 980, 18, 140)
        page.wait_for_timeout(1_000)
        scroll_smooth(page, -300, 8, 120)
        wait_until_mark(page, start, 34)

        safe_click(page, "a.nav-link:has-text('Dashboard')")
        page.wait_for_timeout(1_700)
        clear_and_type(page, "#projectPath", project_path, delay_ms=110)
        safe_click(page, "#tutorialStartBtn")
        page.wait_for_timeout(1_100)
        safe_click(page, "#tutorialNextBtn")
        page.wait_for_timeout(1_100)
        wait_until_mark(page, start, 70)

        safe_click(page, "#auditBtn")
        page.wait_for_timeout(15_000)
        scroll_smooth(page, 980, 14, 130)
        page.wait_for_timeout(1_300)
        sim_boxes = page.locator("input[data-sim-id]")
        if sim_boxes.count() > 0:
            sim_boxes.nth(0).click()
            page.wait_for_timeout(600)
        if sim_boxes.count() > 1:
            sim_boxes.nth(1).click()
            page.wait_for_timeout(800)
        scroll_smooth(page, 840, 10, 120)
        page.wait_for_timeout(1_500)
        scroll_smooth(page, -650, 12, 110)
        wait_until_mark(page, start, 142)

        safe_click(page, "#toggleAdvancedBtn")
        page.wait_for_timeout(700)
        safe_click(page, "#packBtn")
        page.wait_for_timeout(8_500)
        safe_click(page, "#coachBtn")
        page.wait_for_timeout(7_000)
        safe_click(page, "#roadmapBtn")
        page.wait_for_timeout(8_000)
        if page.locator("#artifactList .artifact-item").count() > 0:
            page.locator("#artifactList .artifact-item").first.click()
            page.wait_for_timeout(1_100)
        wait_until_mark(page, start, 190)

        safe_click(page, "#shipBtn")
        page.wait_for_timeout(22_000)
        safe_click(page, "#startTourBtn")
        page.wait_for_timeout(12_000)
        scroll_smooth(page, 700, 10, 120)
        page.wait_for_timeout(1_400)
        wait_until_mark(page, start, 228)

        safe_click(page, "a.nav-link:has-text('Artifacts')")
        page.wait_for_timeout(1_500)
        clear_and_type(page, "#artifactsProjectPath", project_path, delay_ms=95)
        safe_click(page, "#artifactsRefreshBtn")
        page.wait_for_timeout(10_000)
        if page.locator("#artifactsPageList .artifact-item").count() > 0:
            page.locator("#artifactsPageList .artifact-item").first.click()
            page.wait_for_timeout(1_300)
        safe_click(page, "#artifactsCopyBtn")
        page.wait_for_timeout(900)
        safe_click(page, "#artifactsShipBtn")
        page.wait_for_timeout(16_000)
        wait_until_mark(page, start, 262)

        safe_click(page, "a.nav-link:has-text('OpenClaw')")
        page.wait_for_timeout(1_500)
        clear_and_type(page, "#openclawProjectPath", project_path, delay_ms=95)
        safe_click(page, "#openclawProbeBtn")
        page.wait_for_timeout(4_000)
        page.locator("#openclawAction").select_option("audit")
        page.wait_for_timeout(500)
        safe_click(page, "#openclawRunBtn")
        page.wait_for_timeout(6_500)
        safe_click(page, "#openclawCopyCurlBtn")
        page.wait_for_timeout(700)
        safe_click(page, "#openclawCopyRequestBtn")
        page.wait_for_timeout(800)
        wait_until_mark(page, start, 286)

        safe_click(page, "a.nav-link:has-text('Dashboard')")
        page.wait_for_timeout(1_500)
        clear_and_type(page, "#projectPath", project_path, delay_ms=125)
        safe_click(page, "#auditBtn")
        page.wait_for_timeout(11_000)
        wait_until_mark(page, start, 296)
        page.wait_for_timeout(1_500)

        context.close()
        browser.close()

    candidates = sorted(
        temp_video_dir.glob("*.webm"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError(f"Playwright did not produce a video file in {temp_video_dir}")
    raw_path = candidates[0]

    if out_video_path.exists():
        out_video_path.unlink()
    shutil.move(str(raw_path), str(out_video_path))
    if temp_video_dir.exists():
        shutil.rmtree(temp_video_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a ~5-minute Vibe Sentinel click-through with Playwright.")
    parser.add_argument("--project-path", default="demo-repo-video", help="Path typed in the Studio project input.")
    parser.add_argument("--host", default="127.0.0.1", help="Studio host")
    parser.add_argument("--port", type=int, default=8765, help="Studio port")
    parser.add_argument(
        "--output",
        default=".video_assets/walkthrough_raw.webm",
        help="Output raw video path (WebM from Playwright).",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python binary used to start Studio.",
    )
    parser.add_argument(
        "--enable-openclaw",
        action="store_true",
        default=True,
        help="Start Studio with OpenClaw bridge endpoints enabled.",
    )
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    output = Path(args.output).resolve()

    studio_cmd = [
        args.python_bin,
        "-m",
        "vibe_sentinel",
        "studio",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.enable_openclaw:
        studio_cmd.append("--enable-openclaw")

    studio = subprocess.Popen(
        studio_cmd,
        cwd=str(Path(__file__).resolve().parents[1]),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_http(f"{base_url}/index.html")
        run_walkthrough(base_url, args.project_path, output)
    except (RuntimeError, PlaywrightError) as error:
        print(f"recording failed: {error}", file=sys.stderr)
        return 1
    finally:
        studio.terminate()
        try:
            studio.wait(timeout=8)
        except subprocess.TimeoutExpired:
            studio.kill()

    print(f"Recorded walkthrough video: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
