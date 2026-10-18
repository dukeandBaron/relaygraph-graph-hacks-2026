# Demo media

The MP4 in `deliverables/` is an edited walkthrough made from actual browser
captures of the working FalkorDB-backed app, with explanatory captions and local
synthesized English narration. It is explicitly not an uninterrupted screen
recording. `VIDEO_PROVENANCE.json` binds each original capture and the final MP4
to SHA-256 digests. Original capture files are retained unchanged; their display
in the video is resized proportionally without replacing UI content.

The core app does not require these optional media tools. Rebuilding the media
requires Pillow, FFmpeg, Windows fonts and an installed Windows English speech
voice. `render_narration.ps1` consumes `docs/video_scenes.json`; the video builder
consumes the actual UI images. The resulting MP4 was fully decoded with FFmpeg,
and all five caption layouts pass overflow checks. Representative layouts were
visually inspected.

Failed raw screencast experiments are excluded from both the finished video and
the published source snapshot. No private contest account screen, browser
credential, personal document or real user record appears in the demo.
