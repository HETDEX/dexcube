#!/usr/bin/env python3
"""
make_source_lookup.py — Build source-lookup.bin from the HPSC2 catalog.

Enables Detect ID and Source ID search in hetdex-cube-search.html.

Usage:
    python make_source_lookup.py [pdr1_dir] [output]

    pdr1_dir : path to pdr1/ directory (default: /home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/)
    output   : output path (default: ../web/source-lookup.bin)

Output binary format (little-endian):
    8 bytes  : magic "HETSLK\\x00\\x00"
    4 bytes  : N (Uint32) — number of sources
    4 bytes  : padding
    N×4 bytes: source_id_lo  Uint32 — lower 32 bits of source_id, sorted
    N×4 bytes: source_id_hi  Uint32 — upper 32 bits of source_id
    N×4 bytes: detectid_lo   Uint32 — lower 32 bits of detectid
    N×4 bytes: detectid_hi   Uint32 — upper 32 bits of detectid
    N×4 bytes: ra             Float32
    N×4 bytes: dec            Float32
    N×4 bytes: shotid_date    Uint32 — YYYYMMDD part of shotid
    N×2 bytes: shotid_obs     Uint16 — NNN part of shotid
    N×2 bytes: ifuslot_num    Uint16 — ifuslot as integer

Total: 16 + N×32 bytes  (~32 MB for N=1M sources)
Upload source-lookup.bin to the same dexcube/web/ directory on TACC.
"""

import struct
import sys
import os
import glob
import numpy as np


def find_catalog(pdr_dir):
    cat_dir = os.path.join(pdr_dir, 'hetdex_source_catalog_2')
    for pattern in ['hetdex_sc2_v*.fits', 'hetdex_sc2_*.fits']:
        matches = sorted(glob.glob(os.path.join(cat_dir, pattern)))
        if matches:
            return matches[-1]  # latest version
    raise FileNotFoundError(
        f'HPSC2 catalog not found in {cat_dir}\n'
        'Expected: hetdex_sc2_v*.fits'
    )


def convert(pdr_dir, dst):
    from astropy.table import Table

    cat_path = find_catalog(pdr_dir)
    print(f'Reading {cat_path} ...')
    t = Table.read(cat_path)
    N = len(t)
    print(f'  {N:,} sources')

    # Extract required columns
    source_id = np.array(t['source_id'], dtype=np.int64)
    detectid  = np.array(t['detectid'],  dtype=np.int64)
    ra        = np.array(t['RA'],        dtype=np.float32)
    dec       = np.array(t['DEC'],       dtype=np.float32)
    shotid    = np.array(t['shotid'],    dtype=np.int64)

    col = t['ifuslot']
    if col.dtype.kind in ('U', 'S', 'O'):
        ifuslot_num = np.array([int(str(s).strip()) for s in col], dtype=np.uint16)
    else:
        ifuslot_num = np.array(col, dtype=np.uint16)

    # Split 64-bit IDs into two Uint32
    src_lo = (source_id & 0xFFFFFFFF).astype(np.uint32)
    src_hi = ((source_id >> 32) & 0xFFFFFFFF).astype(np.uint32)
    det_lo = (detectid  & 0xFFFFFFFF).astype(np.uint32)
    det_hi = ((detectid  >> 32) & 0xFFFFFFFF).astype(np.uint32)

    shotid_date = (shotid // 1000).astype(np.uint32)
    shotid_obs  = (shotid %  1000).astype(np.uint16)

    # Sort by source_id (lo first for binary-search locality)
    order = np.lexsort((src_hi, src_lo))
    src_lo      = src_lo[order]
    src_hi      = src_hi[order]
    det_lo      = det_lo[order]
    det_hi      = det_hi[order]
    ra          = ra[order]
    dec         = dec[order]
    shotid_date = shotid_date[order]
    shotid_obs  = shotid_obs[order]
    ifuslot_num = ifuslot_num[order]

    print(f'Writing {dst} ...')
    with open(dst, 'wb') as f:
        f.write(b'HETSLK\x00\x00')
        f.write(struct.pack('<II', N, 0))
        f.write(src_lo.tobytes())
        f.write(src_hi.tobytes())
        f.write(det_lo.tobytes())
        f.write(det_hi.tobytes())
        f.write(ra.tobytes())
        f.write(dec.tobytes())
        f.write(shotid_date.tobytes())
        f.write(shotid_obs.tobytes())
        f.write(ifuslot_num.tobytes())

    mb = os.path.getsize(dst) / 1e6
    print(f'Done → {dst}  ({mb:.0f} MB)')
    print()
    print('Upload source-lookup.bin to the dexcube/web/ directory on TACC.')
    print('The page lazy-loads it only when the Detect ID or Source ID tab is used.')


if __name__ == '__main__':
    pdr_dir = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/'
    dst = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(__file__), '..', 'web', 'source-lookup.bin')
    dst = os.path.normpath(dst)
    convert(pdr_dir, dst)
