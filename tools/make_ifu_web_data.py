#!/usr/bin/env python3
"""
make_ifu_web_data.py — Convert ifu-index to compact binary for browser-side cone search.

Usage:
    python make_ifu_web_data.py [input] [output]

    input  : ifu-index.fits  (default)  — also accepts .h5 or .txt/.csv
    output : ifu-data.bin    (default)

Output binary format (little-endian):
    8 bytes  : magic "HETDX2\\x00\\x00"
    4 bytes  : N (Uint32) — number of IFUs
    4 bytes  : padding (zeros)
    N×4 bytes: ra_cen      Float32  — sorted by dec_cen
    N×4 bytes: dec_cen     Float32
    N×4 bytes: shotid_date Uint32   — YYYYMMDD part of shotid
    N×2 bytes: shotid_obs  Uint16   — NNN part of shotid (0–999)
    N×2 bytes: ifuslot_num Uint16   — ifuslot as integer (e.g. '034' → 34)
    N×1 bytes: flag_u8     Uint8    — 0 = bad/flagged, 1 = good (rounded)
    N×1 bytes: field_id    Uint8    — 0=dex-spring 1=dex-fall 2=cosmos
                                       3=goods-n   4=nep      5=ssa22  255=other
    N×1 bytes: fwhm_u8     Uint8    — fwhm_virus × 10  (0.0–25.5 arcsec)
    N×1 bytes: resp_u8     Uint8    — response_4540 × 100 (0.00–2.55)
    N×2 bytes: pa_i16      Int16    — HET tracker PA × 10  (0.1° precision)
                                       DS9 theta = 360 − (90 + pa + 1.55)

Total: 16 + N×22 bytes ≈ 9.5 MB for N=431,713

Deploy ifu-data.bin in the same directory as hetdex-cube-search.html on TACC.
"""

import struct
import sys
import os
import numpy as np

FIELD_MAP = {
    'dex-spring': 0,
    'dex-fall':   1,
    'cosmos':     2,
    'goods-n':    3,
    'nep':        4,
    'ssa22':      5,
}


def read_table(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.fits', '.fit'):
        from astropy.table import Table
        return Table.read(path)
    elif ext in ('.h5', '.hdf5', '.hdf'):
        from astropy.table import Table
        return Table.read(path)
    elif ext in ('.txt', '.csv', '.dat'):
        from astropy.table import Table
        return Table.read(path, format='ascii', guess=True)
    else:
        # Try astropy auto-detect
        from astropy.table import Table
        return Table.read(path)


def convert(src, dst):
    print(f"Reading {src} ...")
    t = read_table(src)
    N = len(t)
    print(f"  {N:,} IFUs")

    ra  = np.array(t['ra_cen'],  dtype=np.float32)
    dec = np.array(t['dec_cen'], dtype=np.float32)

    shotid = np.array(t['shotid'], dtype=np.int64)
    shotid_date = (shotid // 1000).astype(np.uint32)   # YYYYMMDD
    shotid_obs  = (shotid %  1000).astype(np.uint16)   # NNN

    col = t['ifuslot']
    if col.dtype.kind in ('U', 'S', 'O'):
        ifuslot_num = np.array([int(str(s).strip()) for s in col], dtype=np.uint16)
    else:
        ifuslot_num = np.array(col, dtype=np.uint16)

    flag_f = np.array(t['flag'], dtype=np.float32)
    flag_u8 = np.clip(np.round(flag_f), 0, 1).astype(np.uint8)

    if 'field' in t.colnames:
        field_id = np.array(
            [FIELD_MAP.get(str(f).strip(), 255) for f in t['field']],
            dtype=np.uint8
        )
    else:
        field_id = np.full(N, 255, dtype=np.uint8)

    if 'fwhm_virus' in t.colnames:
        fwhm_u8 = np.clip(
            np.round(np.array(t['fwhm_virus'], dtype=np.float32) * 10),
            0, 255
        ).astype(np.uint8)
    else:
        fwhm_u8 = np.zeros(N, dtype=np.uint8)

    if 'response_4540' in t.colnames:
        resp_u8 = np.clip(
            np.round(np.array(t['response_4540'], dtype=np.float32) * 100),
            0, 255
        ).astype(np.uint8)
    else:
        resp_u8 = np.zeros(N, dtype=np.uint8)

    if 'pa' in t.colnames:
        pa_i16 = np.clip(
            np.round(np.array(t['pa'], dtype=np.float32) * 10),
            -32768, 32767
        ).astype(np.int16)
    else:
        pa_i16 = np.zeros(N, dtype=np.int16)

    # Sort by dec for fast binary-search cone queries in JS
    order = np.argsort(dec, kind='stable')
    ra          = ra[order]
    dec         = dec[order]
    shotid_date = shotid_date[order]
    shotid_obs  = shotid_obs[order]
    ifuslot_num = ifuslot_num[order]
    flag_u8     = flag_u8[order]
    field_id    = field_id[order]
    fwhm_u8     = fwhm_u8[order]
    resp_u8     = resp_u8[order]
    pa_i16      = pa_i16[order]

    print(f"Writing {dst} ...")
    with open(dst, 'wb') as f:
        f.write(b'HETDX2\x00\x00')           # magic v2 (8 bytes)
        f.write(struct.pack('<II', N, 0))      # N + padding (8 bytes)
        f.write(ra.tobytes())
        f.write(dec.tobytes())
        f.write(shotid_date.tobytes())
        f.write(shotid_obs.tobytes())
        f.write(ifuslot_num.tobytes())
        f.write(flag_u8.tobytes())
        f.write(field_id.tobytes())
        f.write(fwhm_u8.tobytes())
        f.write(resp_u8.tobytes())
        f.write(pa_i16.tobytes())

    mb = os.path.getsize(dst) / 1e6
    print(f"Done → {dst}  ({mb:.1f} MB)")
    print()
    print("Deploy steps — upload all three files to dexcube/web/ on TACC:")
    print(f"  {dst}")
    print(f"  web/hetdex-cube-search.html")
    print(f"  web/.htaccess")


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'ifu-index.fits'
    dst = sys.argv[2] if len(sys.argv) > 2 else 'ifu-data.bin'
    convert(src, dst)
