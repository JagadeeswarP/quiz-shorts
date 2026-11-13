"""Kokoro-82M narration (Apache-2.0, runs locally, no API). Installs and downloads itself on first use."""
import os, subprocess, sys, urllib.request
from pathlib import Path
import numpy as np

KDIR = Path(os.environ.get('FACELESS_HOME', Path.home() / '.faceless-shorts')) / 'kokoro'
FILES = {
    'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
    'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin',
}
_K = None

def _engine():
    global _K
    if _K: return _K
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        venv = Path.home() / '.faceless-shorts/venv/lib'
        sp = sorted(venv.glob('python*/site-packages')) if venv.exists() else []
        if sp: sys.path.append(str(sp[-1]))
        try:
            from kokoro_onnx import Kokoro
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '--break-system-packages', 'kokoro-onnx'])
            from kokoro_onnx import Kokoro
    KDIR.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        p = KDIR / name
        if not (p.exists() and p.stat().st_size > 1_000_000):
            urllib.request.urlretrieve(url, p)
    _K = Kokoro(str(KDIR / 'kokoro-v1.0.onnx'), str(KDIR / 'voices-v1.0.bin'))
    return _K

def say(text, voice='af_heart', speed=1.18, sr=44100):
    """text -> float32 mono at sr"""
    samples, ksr = _engine().create(text, voice=voice, speed=speed, lang='en-us')
    samples = np.asarray(samples, dtype=np.float32)
    # trim silence
    nz = np.where(np.abs(samples) > 0.01)[0]
    if len(nz): samples = samples[max(0, nz[0] - 200): nz[-1] + 800]
    n = int(len(samples) * sr / ksr)
    return np.interp(np.linspace(0, len(samples) - 1, n), np.arange(len(samples)), samples).astype(np.float32)
