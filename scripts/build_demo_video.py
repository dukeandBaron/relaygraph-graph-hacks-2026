"""Build an explicitly edited walkthrough from actual, unmodified UI captures."""
import hashlib
import json
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

root = Path(__file__).resolve().parents[1]
source = root / 'artifacts/browser'
build = root / 'artifacts/video_build'
build.mkdir(exist_ok=True)
deliverables = root / 'deliverables'
deliverables.mkdir(exist_ok=True)
scenes = json.loads((root / 'docs/video_scenes.json').read_text(encoding='utf-8'))
font_path = Path('C:/Windows/Fonts/segoeui.ttf')
font_bold = Path('C:/Windows/Fonts/seguisb.ttf')
if not font_bold.is_file():
    font_bold = font_path
assert font_path.is_file()
ffmpeg = shutil.which('ffmpeg')
assert ffmpeg

def font(size, bold=False):
    return ImageFont.truetype(str(font_bold if bold else font_path), size)

def text(draw, value, xy, width, size, color, bold=False, spacing=10):
    f = font(size, bold)
    x, y = xy
    line = ''
    for word in value.split():
        candidate = (line + ' ' + word).strip()
        if draw.textlength(candidate, font=f) > width and line:
            draw.text((x, y), line, font=f, fill=color)
            y += size + spacing
            line = word
        else:
            line = candidate
    if line:
        draw.text((x, y), line, font=f, fill=color)
        y += size + spacing
    return y

outputs, evidence = [], []
for number, scene in enumerate(scenes, 1):
    image_path = source / scene['image']
    audio_path = build / 'narration' / (scene['id'] + '.wav')
    assert image_path.is_file() and audio_path.is_file()
    with wave.open(str(audio_path), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate() + 1.2
    board = Image.new('RGB', (1920, 1080), '#eef4f8')
    draw = ImageDraw.Draw(board)
    draw.rectangle((0,0,1920,91), fill='#ffffff')
    draw.text((46, 20), 'RelayGraph', font=font(37, True), fill='#18364b')
    draw.text((1300, 32), 'GRAPH HACKS 2026  /  WORKING UI DEMO', font=font(20), fill='#5a7487')
    draw.rounded_rectangle((37, 117, 1268, 978), radius=12, fill='#ffffff', outline='#ccd9e3', width=2)
    actual = Image.open(image_path).convert('RGB')
    fitted = ImageOps.contain(actual, (1213, 843), method=Image.Resampling.LANCZOS)
    board.paste(fitted, (46 + (1213-fitted.width)//2, 126 + (843-fitted.height)//2))
    draw.text((1320, 147), f'{number} / {len(scenes)}', font=font(24), fill='#007f88')
    y = text(draw, scene['title'], (1317, 206), 535, 49, '#18364b', True, 10)
    y = text(draw, scene['caption'], (1320, y+30), 520, 29, '#4b697e', False, 14)
    details = {
        '01_graph': ['Notice → requirement', 'Task → dependency', 'Owner → review record'],
        '02_preview': ['Catering → travel → registration → deadline', '3 tasks / 4 old records', 'Accessibility stays current'],
        '03_adopt': ['Correction stored as revision 2', 'Old receipt: needs recheck', '3 persistent review actions'],
        '04_sources': ['Exact dependency paths', 'Original notice retained', 'Current values clearly versioned'],
        '05_queries': ['Parameterized Cypher tools', 'Actual database restart verified', 'Read-only MCP context interface'],
    }[scene['id']]
    y += 32
    for detail in details:
        draw.ellipse((1320,y+12,1328,y+20),fill='#007f88')
        y = text(draw, detail, (1347,y), 485, 25, '#28495e', False, 11) + 18
    assert y < 975, ('Caption overflow', scene['id'], y)
    draw.line((45, 1008, 1875, 1008), fill='#c8d7e2', width=2)
    draw.text((47, 1028), 'Edited actual browser captures  ·  Synthetic data  ·  Synthesized narration  ·  AI-assisted development', font=font(21), fill='#526e81')
    png = build / (scene['id'] + '.png')
    board.save(png)
    clip = build / (scene['id'] + '.mp4')
    if clip.exists():
        raise SystemExit('Refuse to overwrite an existing rendered clip: ' + str(clip))
    command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-loop', '1', '-framerate', '15', '-i', str(png), '-i', str(audio_path), '-t', str(round(duration,3)), '-vf', 'format=yuv420p', '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '21', '-threads', '2', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(clip)]
    result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', timeout=120)
    assert result.returncode == 0, result.stderr
    outputs.append(clip)
    evidence.append({'scene': scene['id'], 'actual_ui_capture': str(image_path.relative_to(root)), 'capture_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(), 'seconds': round(duration,3), 'source_capture_file_modified': False, 'display_transform': 'proportional resize; full captured image retained', 'layout_board': str(png.relative_to(root))})
    print(json.dumps({'scene': scene['id'], 'seconds': round(duration,3), 'rendered': True}), flush=True)

concat = build / 'clips.txt'
concat.write_text('\n'.join("file '" + p.as_posix().replace("'", "'\\''") + "'" for p in outputs)+'\n', encoding='utf-8')
final = deliverables / 'RelayGraph_working_demo_20261018.mp4'
if final.exists():
    raise SystemExit('Refuse to overwrite the existing final video')
result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', '-movflags', '+faststart', str(final)], capture_output=True, encoding='utf-8', errors='replace', timeout=60)
assert result.returncode == 0, result.stderr
poster = deliverables / 'RelayGraph_demo_poster.jpg'
Image.open(build / '02_preview.png').convert('RGB').save(poster, quality=92)
receipt = {'video': str(final), 'bytes': final.stat().st_size, 'sha256': hashlib.sha256(final.read_bytes()).hexdigest(), 'format': '1920x1080 H264/AAC', 'mode': 'edited_actual_ui_stills_with_local_synthesized_english_narration', 'uninterrupted_recording_claimed': False, 'paid_model_calls': 0, 'source_captures': evidence, 'raw_failed_recording_used': False}
(deliverables / 'VIDEO_PROVENANCE.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False), flush=True)
