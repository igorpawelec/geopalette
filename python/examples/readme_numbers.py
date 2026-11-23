"""
readme_numbers.py
~~~~~~~~~~~~~~~~~
Print the measured numbers the READMEs state that neither ``www/figures.py``
nor ``r/tools/cross_validate_against_pygeopalette.R`` prints, each line naming
the README statement it backs.

Usage, from anywhere::

    python examples/readme_numbers.py

The pixel sets:

* ``jch`` against ``cam02`` (python/README.md, "``cam02`` is real CIECAM02;
  ``jch`` is not"): every 8-bit sRGB colour, 256 ** 3 pixels, with
  ``rgb_to_cam02`` at its defaults (L_A = 64, Y_b = 20). The hue difference is
  taken between the two hue bands as they come out, as a reader substituting
  one for the other would, on the circle, and only where ``jch`` C > 5: on
  nearly grey pixels the CIECAM02 hue is noise (the maximum is the same 71.1
  degrees for any threshold from 2 to 20).
* Hue on pure greys (r/README.md, "One genuine divergence"): the five pure
  greys of the 1600-pixel set that
  ``r/tools/generate_pygeopalette_reference.py`` builds, rebuilt here with the
  same seed.

The package is read from the checkout this script sits in and need not be
installed; numpy is the only requirement. Nothing is written.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)          # the checkout, not an older installed copy


def srgb_cube():
    """Every 8-bit sRGB colour, as three flat uint8 bands."""
    v = np.arange(256, dtype=np.uint8)
    R, G, B = np.meshgrid(v, v, v, indexing="ij")
    return R.ravel(), G.ravel(), B.ravel()


def reference_set():
    """The 40 x 40 pixels of r/tools/generate_pygeopalette_reference.py."""
    rng = np.random.default_rng(11)
    N = 40
    R = rng.integers(0, 256, (N, N)).astype(np.uint8)
    G = rng.integers(0, 256, (N, N)).astype(np.uint8)
    B = rng.integers(0, 256, (N, N)).astype(np.uint8)
    edge = [
        (0, 0, 0), (255, 255, 255), (128, 128, 128),
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (0, 255, 255), (255, 0, 255),
        (1, 1, 1), (254, 254, 254), (128, 128, 129),
    ]
    for i, (r, g, b) in enumerate(edge):
        R[0, i], G[0, i], B[0, i] = r, g, b
    return R, G, B


def main():
    from pygeopalette import rgb_to_cam02, rgb_to_jch, rgb_to_lchab

    # ---- python/README.md: "cam02 is real CIECAM02; jch is not" ----
    R, G, B = srgb_cube()
    print(f"[python/README.md, cam02 vs jch] pixel set: all {R.size:,} 8-bit sRGB colours, "
          "cam02 at L_A = 64, Y_b = 20")

    J_avg, C_cam, h_cam = (np.asarray(x, dtype=np.float64)
                           for x in rgb_to_cam02(R, G, B, surround="average"))
    J_dark = np.asarray(rgb_to_cam02(R, G, B, surround="dark")[0], dtype=np.float64)
    dJ = np.abs(J_avg - J_dark)
    print(f"[python/README.md] 'J shifts about 8 units between average and dark': "
          f"mean |J_average - J_dark| = {dJ.mean():.2f}, max = {dJ.max():.2f}")
    del J_dark, dJ

    J_jch, C_jch, H_jch = (np.asarray(x, dtype=np.float64) for x in rgb_to_jch(R, G, B))
    rJ = np.corrcoef(J_jch, J_avg)[0, 1]
    rC = np.corrcoef(C_jch, C_cam)[0, 1]
    print(f"[python/README.md] 'tracks CIECAM02 at r ~ 0.98 on J': r = {rJ:.3f}")
    print(f"[python/README.md] '... and 0.89 on C': r = {rC:.3f}")

    dh = np.abs(H_jch - h_cam)
    dh = np.minimum(dh, 360.0 - dh)
    chromatic = C_jch > 5.0
    print(f"[python/README.md] 'its hue can be off by ... degrees': max on pixels with jch C > 5 "
          f"= {dh[chromatic].max():.1f} degrees ({int(chromatic.sum()):,} pixels); "
          f"on all non-grey pixels = {dh[C_jch > 0].max():.1f}")
    del J_avg, C_cam, h_cam, J_jch, C_jch, H_jch, dh, chromatic

    # ---- r/README.md: "One genuine divergence: hue on the neutral axis" ----
    R, G, B = reference_set()
    grey = (R == G) & (G == B)
    Hab = np.asarray(rgb_to_lchab(R, G, B)[2], dtype=np.float64)
    pairs = ", ".join(f"({int(r)},{int(r)},{int(r)}) -> {h:.3f}"
                      for r, h in zip(R[grey], Hab[grey]))
    print(f"[r/README.md, neutral hue] 'on pure greys pygeopalette reports ...': "
          f"Hab on the {int(grey.sum())} pure greys of the {R.size} reference pixels: {pairs}")


if __name__ == "__main__":
    main()
