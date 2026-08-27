# -*- coding: utf-8 -*-
"""Реальный прогон старой _remove_background на маленьком изображении."""
import time
from io import BytesIO

from PIL import Image

from image_processor.services import _remove_background

img = Image.new('RGB', (400, 400), (200, 60, 60))
t0 = time.monotonic()
print('старт remove…', flush=True)
out = _remove_background(img)
print(f'готово за {time.monotonic() - t0:.1f}s, размер {out.size}, режим {out.mode}', flush=True)
