# CLAUDE.md
# This file is automatically read by Claude Code and other LLM coding assistants.
# It provides essential context for working with the HETDEX PDR1 dexcube repository.
# For full survey context, see HETDEX_CONTEXT.md in this repo root.

## What This Repo Is

`dexcube` is a set of 12 sequential Jupyter notebooks for accessing and analysing
HETDEX Public Data Release 1 (PDR1) — 431,713 IFU datacubes covering 86.67 deg²
of optical spectroscopy (3470–5540 Å, R~800) from the Hobby-Eberly Telescope.

The notebooks live in `notebooks/` and must be run in order (01 through 12).
Full survey context (data model, units, bitmask table, catalog schema, file paths)
is in `HETDEX_CONTEXT.md`.

## Critical Facts for Code Generation

### Data paths (set pdr_dir for your environment)
```python
# HETDEX JupyterHub (https://jupyter.tacc.cloud) — data pre-mounted
pdr_dir = '/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/'

# TACC Stockyard (direct filesystem)
pdr_dir = '/corral-repl/utexas/Hobby-Eberly-Telesco/public/HETDEX/pdr/pdr1/'

# Docker container (hetdex/dexcube image)
pdr_dir = '/home/jovyan/work/pdr1/'
```

### Cube file path convention
```python
import os.path as op
path = op.join(pdr_dir, 'datacubes', str(shotid),
               f'dex_cube_{shotid}_{ifuslot}.fits')
```

### Datacube dimensions and units — DO NOT GET THESE WRONG
- Shape: **(1036, 104, 104)** — always fixed. Axes: (wavelength, y, x) in numpy.
- Wavelength: 3470–5540 Å in **2 Å steps**. Use `CRVAL3 + (i - CRPIX3 + 1) * CDELT3`.
- DATA units: **10⁻¹⁷ erg s⁻¹ cm⁻² per 2 Å bin** (NOT per Å).
  - Divide by 2 to get flux density in erg/s/cm²/Å.
  - Multiply by 1e-17 to get CGS.
- ERROR: same units as DATA (1σ per spaxel per 2 Å bin).
- NaN = outside valid fiber region (expected at cube edges).

### HDU structure
```
HDU 0: PRIMARY  — empty
HDU 1: DATA     — flux (1036, 104, 104)
HDU 2: ERROR    — 1-sigma uncertainty (1036, 104, 104)
HDU 3: MASK     — bitmask flags (1036, 104, 104)
```

### Masking — always apply at minimum
```python
# Minimum required mask (MAIN + FTF + CHI2FIB + BADPIX + BADAMP = bits 1+2+4+8+16)
good = (mask & (1 | 2 | 4 | 8 | 16)) == 0

# Full mask for faint emission-line searches
good = mask == 0
```

**Bitmask convention: 0 = GOOD. Non-zero = flagged.** This is the OPPOSITE of the
`flag` column in `ifu-index.fits`, where `flag = 1 = good, flag = 0 = bad`.

### WCS — always use naxis=2 for spatial coordinates
```python
from astropy.wcs import WCS
wcs2d = WCS(hdul['DATA'].header, naxis=2)
# Cubes are NOT north-up. Always use WCS, never assume pixel orientation.
# ADR is already corrected in the public cubes.
```

### Finding cubes by coordinate
```python
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

ifu = Table.read(op.join(pdr_dir, 'ifu-index.fits'))
ifu_coords = SkyCoord(ra=ifu['ra_cen']*u.deg, dec=ifu['dec_cen']*u.deg)
target = SkyCoord(ra=RA*u.deg, dec=DEC*u.deg)
sel = target.separation(ifu_coords) < 37*u.arcsec  # IFU radius ~26"
```

### Source catalog (HPSC2)
- Main file: `hetdex_source_catalog_2/hetdex_sc2_vX.X.fits`
- Key columns: `source_id`, `RA`, `DEC`, `z_hetdex`, `source_type`, `flux_lya`,
  `flux_oii`, `p_conf`, `p_cnn`
- `source_type` values: `'lae'`, `'oii'`, `'agn'`, `'lzg'`, `'star'`
- Recommended quality cut: `p_conf >= 0.5` and `p_cnn >= 0.5`
- Flux units: **10⁻¹⁷ erg s⁻¹ cm⁻²** (same as DATA extension)
- Bad values: `-999.0` for floats, `'n/a'` for strings

## Common Mistakes to Avoid

1. **Wrong flux units**: DATA is per 2 Å bin, not per Å. Divide by 2 for flux density.
2. **Wrong mask convention**: `mask == 0` is good in the MASK HDU; `flag == 1` is good
   in the ifu-index.
3. **Hardcoded paths**: always use `pdr_dir` as a variable, not absolute paths.
4. **North-up assumption**: cubes are rotated to HET PA — always use WCS.
5. **ADR correction**: already applied — do not correct again.
6. **2017 data**: low quality, avoid for LAE science.
7. **Intensity mapping / extended emission**: local sky subtraction in PDR1 is not
   suitable for absolute surface-brightness measurements.

## Notebook Sequence

01 Data model → 02 Download → 03 Cube format → 04 Masking → 05 CubeWidget →
06 Coordinate query → 07 Collapsing → 08 Spectral extraction →
09 Catalog extractions → 10 Source catalog → 11 Source look-up → 12 Batch download

## Key External Links

- Data portal: https://hetdex.org/data-results/
- JupyterHub: https://jupyter.tacc.cloud
- PDR1 base URL: https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/
- HPSC2 Zenodo: https://doi.org/10.5281/zenodo.19581262
- Contact: erin.hetdex@gmail.com
