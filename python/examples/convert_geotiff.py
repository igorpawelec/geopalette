"""
convert_geotiff.py
~~~~~~~~~~~~~~~~~~
Convert the orthophoto in ``test_data/`` to a colour space, write the result as
a GeoTIFF and save a side-by-side picture of the input and the output.

Usage, from anywhere::

    python examples/convert_geotiff.py [space]

``space`` is one of ``pygeopalette.available_spaces()``; the default is ``lab``.
The outputs go to ``results/<space>/`` in the package folder. The package is
read from the checkout this script sits in and need not be installed; numpy,
rasterio and matplotlib do.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INPUT = os.path.join(ROOT, "test_data", "SNP_21_2020_1.tif")
BASE_OUT = os.path.join(ROOT, "results")
sys.path.insert(0, ROOT)          # the checkout, not an older installed copy


def main(space="lab"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import rasterio
    from pygeopalette import available_spaces, convertbands
    from pygeopalette.io_utils import convert_raster

    print(f"Available spaces: {available_spaces()}")

    out_dir = os.path.join(BASE_OUT, space)

    # The file: every band named after its component, no-data kept as no-data.
    multi_path = convert_raster(INPUT, out_dir, space)

    # The same conversion on arrays, for the picture.
    with rasterio.open(INPUT) as src:
        R, G, B = src.read(1), src.read(2), src.read(3)
        valid = src.dataset_mask() != 0
    comps, names = convertbands(R, G, B, space)
    print(f"Converted to {space}: components = {names}")

    def stretch(ch):
        lo, hi = np.percentile(ch[valid], (2, 98))
        return np.clip((ch - lo) / (hi - lo + 1e-8), 0, 1)

    orig = np.dstack((R, G, B)) / 255.0
    conv = np.dstack([stretch(np.asarray(c, dtype="float64")) for c in comps[:3]])
    conv[~valid] = 1.0
    orig[~valid] = 1.0

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    ax[0].imshow(orig)
    ax[0].set_title("RGB")
    ax[0].axis("off")
    ax[1].imshow(conv)
    ax[1].set_title(f"{space}: {', '.join(names[:3])} as red, green, blue")
    ax[1].axis("off")
    plt.tight_layout()
    picture = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(INPUT))[0]}_{space}.png")
    fig.savefig(picture, dpi=120)
    print(f"Saved: {multi_path}")
    print(f"Saved: {picture}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
