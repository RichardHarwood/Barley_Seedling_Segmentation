#!/usr/bin/env python3
"""
tile_random_subset.py
===========================================================================
Create a SMALL random sample of 1024 x 1024 tiles for quick inspection /
annotation, rather than exhaustively tiling every image.

What it does
------------
1. Picks N (default 10) random images from ``processed_JPG_subset``.
2. Crops ONE random, grid-aligned 1024 x 1024 tile from each chosen image.
3. Saves the tiles into a ``tiled_imgs`` folder.

Paths
-----
The base directory defaults to the *current working directory* in WSL, i.e.
the repo root this ``scripts`` folder lives in:

    <repo>/USYD_20250705/processed_JPG_subset   <- input images
    <repo>/USYD_20250705/tiled_imgs             <- output tiles

Override any path / option from the command line (see ``--help``).

Usage
-----
    python scripts/tile_random_subset.py
    python scripts/tile_random_subset.py --n-images 10 --seed 42
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image

# These are large (trusted) camera images, so lift Pillow's decompression-bomb
# guard to silence the warning on big files.
Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
# Default configuration
# --------------------------------------------------------------------------- #
# Base dir = repo root = parent of the "scripts" folder this file lives in.
# This resolves relative to the script, so it works from any current dir.
BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_INPUT_DIR = BASE_DIR / "USYD_20250705" / "processed_JPG_subset"
DEFAULT_OUTPUT_DIR = BASE_DIR / "USYD_20250705" / "tiled_imgs"

TILE_SIZE = 1024          # tile width & height in pixels (square)
N_IMAGES = 10             # number of random images to sample
DEFAULT_SEED = 7          # fixed seed -> reproducible run with no CLI args
VALID_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def list_images(input_dir: Path) -> list[Path]:
    """Return all image files in *input_dir* (non-recursive, sorted)."""
    return sorted(
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTS
    )


def random_tile(img: Image.Image, tile: int, rng: random.Random):
    """Crop one random, grid-aligned ``tile`` x ``tile`` square from *img*.

    Returns ``(cropped_image, (col, row))`` or ``None`` if the image is
    smaller than a single tile in either dimension.
    """
    w, h = img.size
    n_cols, n_rows = w // tile, h // tile
    if n_cols < 1 or n_rows < 1:
        return None
    col = rng.randint(0, n_cols - 1)
    row = rng.randint(0, n_rows - 1)
    box = (col * tile, row * tile, (col + 1) * tile, (row + 1) * tile)
    return img.crop(box), (col, row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_DIR,
                        help="Folder containing the source images.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Folder to write the sampled tiles to.")
    parser.add_argument("--tile-size", type=int, default=TILE_SIZE,
                        help="Tile size in pixels (square). Default: 1024.")
    parser.add_argument("--n-images", type=int, default=N_IMAGES,
                        help="Number of random images to sample. Default: 10.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"Random seed for reproducible sampling. "
                             f"Default: {DEFAULT_SEED}.")
    parser.add_argument("--no-clean", action="store_true",
                        help="Keep existing tiles instead of clearing the "
                             "output folder first.")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    input_dir: Path = args.input
    output_dir: Path = args.output

    if not input_dir.is_dir():
        raise SystemExit(f"[error] Input folder not found: {input_dir}")

    images = list_images(input_dir)
    if not images:
        raise SystemExit(f"[error] No images found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear any existing tiles first (equivalent to `rm -f tiled_imgs/*.jpg`),
    # so each run starts from a clean folder. Use --no-clean to keep them.
    if not args.no_clean:
        removed = 0
        for old in output_dir.glob("*.jpg"):
            old.unlink()
            removed += 1
        if removed:
            print(f"[clean] Removed {removed} existing tile(s) from {output_dir}")

    # Can't sample more images than we actually have.
    k = min(args.n_images, len(images))
    if k < args.n_images:
        print(f"[warn] Only {len(images)} image(s) available; sampling {k}.")
    chosen = rng.sample(images, k)

    print(f"Input : {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Tiles : 1 random {args.tile_size}x{args.tile_size} tile from "
          f"{k} random image(s)\n")

    saved = 0
    for src in chosen:
        with Image.open(src) as im:
            im = im.convert("RGB")
            result = random_tile(im, args.tile_size, rng)
        if result is None:
            print(f"[skip] {src.name}: smaller than a {args.tile_size}px tile.")
            continue
        tile_img, (col, row) = result
        out_name = f"{src.stem}_tile_c{col}_r{row}.jpg"
        tile_img.save(output_dir / out_name, quality=95)
        saved += 1
        print(f"[ok]   {src.name} -> {out_name}")

    print(f"\nDone. Saved {saved} tile(s) to: {output_dir}")

    # List the output folder contents (equivalent to `ls -la tiled_imgs`).
    print("\n---- contents of tiled_imgs ----")
    for p in sorted(output_dir.iterdir()):
        size = p.stat().st_size
        print(f"{size:>12,d}  {p.name}")


if __name__ == "__main__":
    main()
