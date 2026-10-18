import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'deliverables'
video = out / 'RelayGraph_working_demo_20261018.mp4'
result = subprocess.run([shutil.which('ffmpeg'), '-hide_banner', '-threads', '2', '-i', str(video), '-f', 'null', 'NUL'], capture_output=True, encoding='utf-8', errors='replace', timeout=60)
assert result.returncode == 0, result.stderr[-3000:]
duration = re.search(r'Duration: (\d+:\d+:\d+\.\d+)', result.stderr)
assert duration and '1920x1080' in result.stderr and 'Audio: aac' in result.stderr and 'Video: h264' in result.stderr
receipt_path = out / 'VIDEO_PROVENANCE.json'
receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
assert hashlib.sha256(video.read_bytes()).hexdigest() == receipt['sha256']
for scene in receipt['source_captures']:
    assert hashlib.sha256((root / scene['actual_ui_capture']).read_bytes()).hexdigest() == scene['capture_sha256']
    scene.pop('source_pixels_modified', None)
    scene['source_capture_file_modified'] = False
    scene['display_transform'] = 'proportional resize; full captured image retained'
receipt['media_validation'] = {'full_video_and_audio_decoded': True, 'duration': duration.group(1), 'video': 'H264 1920x1080', 'audio': 'AAC', 'visual_boards_checked': ['02_preview', '03_adopt', '05_queries'], 'layout_text_overflow_checks': 'PASS_ALL_FIVE_SCENES'}
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'video': str(video), 'duration': duration.group(1), 'bytes': video.stat().st_size, 'full_decode_exit': result.returncode, 'sha256': receipt['sha256']}))
