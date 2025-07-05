import json
import subprocess
from pathlib import Path

from vision.detect import main


def test_detect(tmp_path):
    video = Path("data/sample_clip.mp4")
    if not video.exists():
        video.parent.mkdir(exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=128x128:d=2",
                str(video),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    output = tmp_path / "detections.json"
    main(["--video", str(video), "--output", str(output)])

    assert output.exists()
    assert output.stat().st_size > 0
    data = json.loads(output.read_text())
    assert isinstance(data, list)
