#!/usr/bin/env python3
"""
Prepares the source photo for clean, high-contrast monochrome ASCII art:
  1. Grayscale conversion
  2. Edge-preserving contrast enhancement
  3. Gamma adjustment to balance hair texture, silhouette, and facial highlights
  4. Unsharp mask sharpening to keep fine lines sharp at ascii resolution
Outputs: source-prepped.png
"""
import os
import sys
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

def prep_image(input_path, output_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    im = Image.open(input_path).convert("RGB")
    # Grayscale
    gray = im.convert("L")

    # Autocontrast to span full 0-255 dynamic range
    contrast = ImageOps.autocontrast(gray, cutoff=(1, 1))

    # Brighten midtones slightly to bring out shadows & hair waves
    contrast = ImageEnhance.Brightness(contrast).enhance(1.15)
    contrast = ImageEnhance.Contrast(contrast).enhance(1.35)

    # Sharp edge enhancement
    sharp = contrast.filter(ImageFilter.UnsharpMask(radius=2.2, percent=150, threshold=2))

    sharp.save(output_path, "PNG")
    print(f"Prepped image saved to {output_path} ({sharp.size})")

if __name__ == "__main__":
    prep_image(INP, OUT)
