# HETDEX_CONTEXT.md
# Machine-readable context for LLM-assisted scientific analysis of HETDEX PDR1
# Reference paper: Mentuch Cooper et al. 2026 — "HETDEX Public Data Release 1:
#   Source Catalog 2 and Datacubes from ~90 deg2 of Integral-Field Optical Spectroscopy"
# Maintained by: Erin Mentuch Cooper (erin.hetdex@gmail.com)
# Last updated: 2026-04-22
# Source repo: https://github.com/HETDEX/dexcube

---

## 1. Survey Overview

**HETDEX** (Hobby-Eberly Telescope Dark Energy Experiment) is a blind, untargeted
integral field unit (IFU) spectroscopic survey conducted at McDonald Observatory
using the Hobby-Eberly Telescope (HET) and the VIRUS instrument. Its primary
scientific goal is to constrain dark energy via baryonic acoustic oscillations
(BAO), measured through the 3D positions of Lyman-alpha emitting galaxies (LAEs)
at redshifts 1.88 < z < 3.52.

- **Telescope**: Hobby-Eberly Telescope (HET), 10-metre effective aperture
- **Instrument**: VIRUS — up to 78 IFUs, each feeding a pair of spectrographs
  with 448 x 1.5"-diameter fibers; ~35,000 spectra per exposure
- **IFU field of view**: 51" x 51" per IFU
- **VIRUS fill factor**: 0.22 (1/4.6) of the HET's 22'-diameter focal plane
- **Wavelength coverage**: 3470-5540 Angstroms (observed frame, in air)
- **Spectral resolution**: R ~ 750-950 (FWHM ~ 4.7-5.6 Ang); median R ~ 800
- **Spectral sampling**: 2 Ang per pixel
- **Median image quality**: FWHM ~ 1.8 arcsec
- **Exposure time per field**: ~1200 s total (3 dithered exposures of 6-7 min each)
- **Survey dates**: Science verification started January 2017; main survey
  December 2017 - July 2024; survey complete
- **Total survey footprint**: ~540 deg^2 (Spring + Fall fields)
- **PDR1 sky coverage**: 86.67 deg^2 of non-contiguous sky across 431,713 IFU
  datacubes from 6778 observations

### Survey Fields (PDR1)

| Field ID   | Centre (RA, Dec)      | Footprint area | N(IFU)  | N(LAE)  |
|------------|-----------------------|----------------|---------|---------|
| dex-spring | (195.00 deg, +51.00)  | ~390 deg^2     | 244,176 | 253,458 |
| dex-fall   | (22.50 deg, +0.00)    | ~150 deg^2     | 136,829 | 114,419 |
| nep        | (270.00 deg, +66.00)  | 6.88 deg^2     | 34,269  | 25,649  |
| cosmos     | (150.12 deg, +2.21)   | 2.26 deg^2     | 11,271  | 7,794   |
| ssa22      | (336.50 deg, +0.00)   | 0.88 deg^2     | 4,393   | 3,975   |
| goods-n    | (189.18 deg, +62.24)  | 0.16 deg^2     | 775     | 1,025   |
| **total**  |                       | **86.64 deg^2**| 431,713 | 406,320 |

The two primary fields (dex-spring at 13h +51 deg, dex-fall at 1.5h 0 deg) are
at high Galactic latitude to minimise dust and stellar contamination. PDR1 also
includes legacy fields: NEP (Texas Euclid Survey for Lya), COSMOS, SA22, GOODS-N.

### Wavelength Notes

- All spectral data are in **air** wavelengths.
- Redshifts are calculated from rest-frame wavelengths with air-to-vacuum
  conversion (Greisen et al. 2006) and include a barycentric velocity correction.
- Rest-frame vacuum wavelength of Lya: 1215.67 Ang
- Rest-frame air wavelength of [O II] doublet: 3727.8 Ang (integrated to VIRUS resolution)

---

## 2. Public Data Release 1 (PDR1)

PDR1 covers all science-quality HETDEX observations from 2017-01-01 to 2024-07-31,
drawn from the fifth internal data release (HDR5). Full public release: 2026.

- **Number of IFU datacubes**: 431,713
- **Number of observations (shotids)**: 6,778
- **Total data volume**: ~9.8 TB (datacubes: 7.4 TB; raw detections: 1.7 TB)
- **Each cube size**: ~19 MB
- **PDR1 base URL**: https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/
- **Catalog URL**: https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/hetdex_source_catalog_2/
- **HPSC2 Zenodo DOI**: https://doi.org/10.5281/zenodo.19581262

### Data Path by Environment

```python
# TACC Stockyard (direct filesystem access)
pdr_dir = '/corral-repl/utexas/Hobby-Eberly-Telesco/public/HETDEX/pdr/pdr1/'

# HETDEX JupyterLab (https://jupyter.tacc.cloud)
pdr_dir = '/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/'

# Docker container (hetdex/dexcube image)
pdr_dir = '/home/jovyan/work/pdr1/'
```

### File Path Convention for Datacubes

```python
import os.path as op
cube_path = op.join(pdr_dir, 'datacubes', str(shotid),
                    f'dex_cube_{shotid}_{ifuslot}.fits')
# Example: pdr1/datacubes/20190405020/dex_cube_20190405020_034.fits
```

---

## 3. Datacube Format

Each PDR1 product is a single FITS file for one IFU observation. Atmospheric
differential refraction (ADR) **is corrected** during cube generation -- the ADR
correction is applied per wavelength slice before resampling the fiber positions
onto the output spatial grid using SciPy griddata linear interpolation.

### FITS HDU Structure (Table 2 in PDR1 paper)

| HDU Index | EXTNAME | Description                                                    | Shape          |
|-----------|---------|----------------------------------------------------------------|----------------|
| 0         | PRIMARY | Primary HDU with no data                                       | None           |
| 1         | DATA    | Flux in 10^-17 erg/s/cm^2 per 2 Ang spectral bin              | (1036, 104, 104) |
| 2         | ERROR   | 1-sigma uncertainty (same units as DATA)                       | (1036, 104, 104) |
| 3         | MASK    | Bitmask quality flags per spaxel                               | (1036, 104, 104) |

**All cubes have identical fixed dimensions: (1036, 104, 104)**
- Wavelength axis (numpy axis 0): 1036 pixels, 3470-5540 Ang in 2 Ang steps
- Spatial axes (numpy axes 1 and 2): 104 x 104 spaxels at 0.5 arcsec/spaxel = 52" x 52"

### Units

- **DATA**: 10^-17 erg s^-1 cm^-2 per 2 Ang spectral bin (NOT per Ang)
  - To convert to flux density (erg/s/cm^2/Ang): divide DATA by 2.0
  - To convert to CGS (erg/s/cm^2): multiply DATA by 1e-17
- **ERROR**: same units as DATA (1-sigma per spaxel per 2 Ang bin)
- Spaxels outside the valid fiber region are assigned **NaN**

### Key Header Keywords

| Keyword    | Description                                                           |
|------------|-----------------------------------------------------------------------|
| CRPIX1/2   | Reference pixel, spatial (1-indexed, at pixel center, FITS convention)|
| CRVAL1/2   | Reference RA, Dec (degrees, ICRS J2000)                               |
| CD1_1 etc  | WCS CD matrix; encodes IFU position angle on sky                      |
| CRPIX3     | Reference pixel, wavelength axis                                      |
| CRVAL3     | Reference wavelength (Ang)                                            |
| CDELT3     | Wavelength dispersion = 2.0 Ang/pixel                                 |
| CTYPE3     | 'WAVE' or 'LINEAR'                                                    |
| EXPTIME    | Total exposure time (s)                                               |
| SHOTID     | Unique observation ID (integer YYYYMMDDNNN)                           |
| IFUSLOT    | IFU slot string identifier                                            |

### Coordinate System Notes

- **Orientation**: Cubes are aligned to the HET tracker rotation angle, NOT
  north-up/east-left. Always use WCS headers. Use `astropy.wcs.WCS(header, naxis=2)`
  for spatial-only WCS.
- **Wavelength axis in numpy**: axis 0, i.e. `DATA[wave_index, y_index, x_index]`
- **WCS pixel convention**: CRPIXn values are 1-indexed at pixel centers (FITS standard)
- **ADR correction**: Already applied per wavelength slice during cube generation.

### Getting the Wavelength Array

```python
import numpy as np
from astropy.io import fits

hdul = fits.open('dex_cube_XXXXXXXX_XXX.fits')
hdr = hdul['DATA'].header
wave = hdr['CRVAL3'] + (np.arange(hdul['DATA'].data.shape[0])
                         - hdr['CRPIX3'] + 1) * hdr['CDELT3']
# wave is in Angstroms, 3470 to 5540 in steps of 2
```

---

## 4. Bitmask Definitions (Table 3 in PDR1 paper)

The MASK extension (HDU3) is a bitmask integer array. A spaxel is flagged for a
condition if the corresponding bit is set. Test with `(mask & VALUE) > 0`.

**Critical convention note**: In the MASK HDU, `0 = GOOD` (no flag set). This is
the OPPOSITE of the `flag` column in the IFU index table, where `flag = 1 = good`.

| Hex Value   | Integer | Name       | Description                                               | Usage           |
|-------------|---------|------------|-----------------------------------------------------------|-----------------|
| 0x00000000  | 0       | Good       | No flag -- data is usable                                 | --              |
| 0x00000001  | 1       | MAIN       | Flagged in pipeline reduction (calfibe == 0.0)            | **Always mask** |
| 0x00000002  | 2       | FTF        | Fiber-to-fiber deviation in spectrum > 0.5                | **Always mask** |
| 0x00000004  | 4       | CHI2FIB    | chi2fib > 150 (poor fiber profile fit)                    | **Always mask** |
| 0x00000008  | 8       | BADPIX     | On a bad pixel region                                     | **Always mask** |
| 0x00000010  | 16      | BADAMP     | On a bad amplifier                                        | **Always mask** |
| 0x00000020  | 32      | LARGEGAL   | Within large galaxy or planetary nebula mask              | Science-dep.    |
| 0x00000040  | 64      | METEOR     | On a known meteor track                                   | **Always mask** |
| 0x00000080  | 128     | BADSHOT    | In bad shot list (not present in PDR1 public cubes)       | N/A             |
| 0x00000100  | 256     | THROUGHPUT | Throughput at 4540 Ang < 0.08 (not present in PDR1)       | N/A             |
| 0x00000200  | 512     | BADFIB     | On a known bad fiber                                      | **Always mask** |
| 0x00000400  | 1024    | SAT        | On a known satellite track                                | Recommended     |
| 0x00000800  | 2048    | BADCAL     | Sky/calibration issue at this wavelength                  | Science-dep.    |
| 0x00001000  | 4096    | PIXMASK    | Native spectrum counts == 0                               | **Always mask** |
| 0x00002000  | 8192    | BADDET     | 5x5x5 pixel mask at flagged detection location            | Emission searches|

### Recommended Masking Strategies

**Minimum mask** -- always apply for any science use (MAIN + FTF + CHI2FIB + BADPIX + BADAMP):
```python
good = (mask & (1 | 2 | 4 | 8 | 16)) == 0
```

**Full science mask** -- recommended for faint emission-line source detection:
```python
good = mask == 0
```

**BADCAL flagged spectral windows** (always masked per observation):
- 3534-3556 Ang: persistent sky line, masked in every observation
- 5194-5197 Ang and 5200-5205 Ang: sharp sky feature (amplifier/shot-dependent)
- 5456-5466 Ang: sky line (amplifier/shot-dependent)

BADCAL can be safely ignored for bright sources: stars, nearby galaxies, most AGN.

---

## 5. IFU Index File

The **IFU index** (`ifu-index.fits`, also available as `.h5` and `.txt`) is the
master look-up table for all PDR1 datacubes. Every row is one IFU observation.
The `shotid`/`ifuslot` combination uniquely identifies each cube.

**File location**: `pdr_dir/ifu-index.fits`
Direct URL: https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/ifu-index.fits

### Key Columns (Table 6 in PDR1 paper)

| Column         | Type    | Units  | Description                                                      |
|----------------|---------|--------|------------------------------------------------------------------|
| shotid         | int64   | --     | Observation ID integer (YYYYMMDDNNN form)                        |
| ifuslot        | str     | --     | IFU slot identifier string (e.g., '046', '063')                  |
| ra_cen         | float32 | deg    | RA of IFU center (ICRS J2000)                                    |
| dec_cen        | float32 | deg    | Dec of IFU center (ICRS J2000)                                   |
| flag           | float32 | --     | **flag=1 = fully useable; flag=0 = fully flagged** (1=good!)     |
| flag_badamp    | float32 | --     | Fraction of IFU unaffected by bad amplifier(s)                   |
| flag_badfib    | float32 | --     | Fraction of IFU unaffected by bad fiber(s)                       |
| flag_meteor    | float32 | --     | Fraction of IFU unaffected by meteor trail                       |
| flag_satellite | float32 | --     | Fraction of IFU unaffected by satellite trail                    |
| flag_shot      | float32 | --     | Fraction of IFU unaffected by shot-level flagging                |
| flag_throughput| float32 | --     | Fraction of IFU unaffected by low throughput                     |
| field          | str     | --     | 'dex-spring', 'dex-fall', 'cosmos', 'goods-n', 'nep', 'ssa22'  |
| fwhm_virus     | float32 | arcsec | Seeing FWHM measured from VIRUS stars                            |
| fwhm_virus_err | float32 | arcsec | Uncertainty in seeing measurement                                |
| response_4540  | float32 | --     | Normalised system throughput at 4540 Ang (360 s reference)       |
| mjd            | float32 | days   | Modified Julian Date                                             |
| exptime        | float32 | s      | Exposure time                                                    |
| pa1            | float64 | deg    | HET tracker rotation angle; PA (E of N) = 360 - (90 + pa + 1.55)|
| n_ifu          | int32   | --     | Number of active IFUs in the shot                                |
| ra_shot        | float64 | deg    | RA of shot centre (ICRS J2000)                                   |
| dec_shot       | float64 | deg    | Dec of shot centre (ICRS J2000)                                  |

**PDR1 flag statistics**: 91.6% of cubes are fully unflagged; 7.8% flagged for bad
amplifiers, 0.2% bad fibers, 0.12% satellites, 0.04% meteors.

### Coordinate Query Example (Section 4.5.1 in PDR1 paper)

```python
import os.path as op
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

pdr_dir = '/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/'

# Load IFU index
ifu_data = Table.read(op.join(pdr_dir, 'ifu-index.fits'))

# Create SkyCoord array of IFU centers
ifu_coords = SkyCoord(ra=ifu_data['ra_cen']*u.deg,
                      dec=ifu_data['dec_cen']*u.deg)

# Target coordinate (example: a Lya nebula at z=2.53)
coord = SkyCoord(ra=228.78581*u.deg, dec=51.268036*u.deg)

# Select IFUs within 37 arcsec of target (IFU radius ~ 26 arcsec)
sel = coord.separation(ifu_coords) < 37*u.arcsec

# Build file paths for matching cubes
for row in ifu_data[sel]:
    shotid  = row['shotid']
    ifuslot = row['ifuslot']
    path = op.join(pdr_dir, 'datacubes', str(shotid),
                   f'dex_cube_{shotid}_{ifuslot}.fits')
    print(path)
```

---

## 6. Source Populations (HPSC2)

PDR1 includes the **HETDEX Public Source Catalog 2 (HPSC2)**, an expanded and
reprocessed version of HPSC1 (Mentuch Cooper et al. 2023). HPSC2 applies selection
thresholds of p_conf >= 0.5 AND p_cnn >= 0.5 for a robust catalog.

### Source Counts by Type (full PDR1 total, Table 1 in PDR1 paper)

| source_type | Count     | Redshift range  | Primary line / method                |
|-------------|-----------|-----------------|--------------------------------------|
| lae         | 426,654   | 1.88 < z < 3.52 | Lya 1215.67 Ang (vacuum)             |
| oii         | 491,411   | 0 < z < 0.48    | [O II] 3727.8 Ang doublet            |
| agn         | 18,303    | 0 < z < 4.6     | Broad lines / AGN catalog Liu+2025   |
| lzg         | 19,457    | 0 < z < 0.5     | Continuum template (no emission)     |
| star        | 150,608   | z = 0           | Stellar templates (Diagnose)         |
| **total**   | **1,085,129** |             |                                      |

**Note on LAE sample**: The full LAE candidate database contains 1,632,604 sources.
HPSC2 applies p_conf >= 0.5 and p_cnn >= 0.5 to reduce this to 426,654. The full
candidate list (including low-confidence) is in the Supplemental Detection Info Table.

### Classification Methods and Priority Order

1. **HETDEX AGN Catalog** (Liu et al. 2022, 2025): Targeted broad-line search;
   takes priority for all AGN.
2. **Diagnose** (Debski & Zeimann 2024): PCA template fitting for g < 22 sources;
   classifies star, galaxy, qso; ~97% reliable at g_HETDEX < 22.
3. **ELiXer** (Davis et al. 2023a): Bayesian line identification using equivalent
   widths, broadband imaging, and luminosity priors. Assigns P(Lya) threshold 0.4
   for LAE vs [O II] discrimination. Overall redshift accuracy ~96%; catastrophic
   outlier fraction 5.9% (|dz|/(1+z) > 0.2).

### ML/AI Quality Classifiers

| Column | Description                                                                |
|--------|----------------------------------------------------------------------------|
| p_conf | Random Forest LAE confidence score (0-1); **1 = high confidence, 0 = low**|
| p_cnn  | CNN LAE/faint-OII confidence score (0-1); **1 = high confidence, 0 = low** |

HPSC2 contains sources with p_conf >= 0.5 AND p_cnn >= 0.5. For statistical LAE
studies the recommended threshold is p_conf >= 0.5 and p_cnn >= 0.5.

---

## 7. HPSC2 Catalog Schema

### Main Catalog: hetdex_sc2_vX.X.fits / .dat (Table 5 in PDR1 paper)

One row per source observation. If a source is observed in multiple shots, it
appears multiple times with the same source_name but different source_id values.

| Column         | Description                                                                     |
|----------------|---------------------------------------------------------------------------------|
| source_name    | HETDEX IAU designation (e.g., HETDEX J123449.19+511733.7)                      |
| source_id      | Unique source identifier (integer; per observation)                             |
| shotid         | Integer observation ID: int(date + obsid)                                       |
| ifuslot        | String IFU identifier in focal plane                                            |
| RA             | Source RA (ICRS J2000, degrees)                                                 |
| DEC            | Source Dec (ICRS J2000, degrees)                                                |
| RA_det         | Representative detectid RA (ICRS J2000)                                         |
| DEC_det        | Representative detectid Dec (ICRS J2000)                                        |
| gmag           | SDSS g magnitude from HETDEX spectrum                                           |
| Av             | Applied V-band extinction correction                                             |
| z_hetdex       | HETDEX spectroscopic redshift                                                    |
| z_hetdex_src   | Method used for redshift                                                         |
| z_hetdex_conf  | Confidence (0-1) in redshift                                                    |
| source_type    | One of: 'star', 'lae', 'agn', 'lzg', 'oii'                                    |
| detectid       | Representative detection ID (selected_det==True in Detection Info Table)        |
| field          | 'dex-fall', 'dex-spring', 'cosmos', 'goods-n', 'nep', 'ssa22'                 |
| flux           | Extinction-corrected line flux (10^-17 erg/s/cm^2); -999 for continuum sources |
| flux_err       | MCMC error on flux                                                              |
| flux_aper      | Extinction-corrected [O II] aperture flux (10^-17 erg/s/cm^2)                  |
| flux_aper_err  | Uncertainty in flux_aper                                                        |
| flag_aper      | **1** = use flux_aper for lum_oii; **0** = use PSF flux; **-1** = no [O II]    |
| major          | Major axis (arcsec) of resolved [O II] aperture ellipse                         |
| minor          | Minor axis (arcsec) of resolved [O II] aperture ellipse                         |
| theta          | Position angle (deg) of aperture ellipse                                        |
| logL_lya       | log10 Lya luminosity (erg/s), extinction-corrected                              |
| logL_lya_err   | Uncertainty in logL_lya                                                         |
| logL_oii       | log10 [O II] luminosity (erg/s)                                                 |
| logL_oii_err   | Uncertainty in logL_oii                                                         |
| flux_lya       | Lya flux (10^-17 erg/s/cm^2), extinction-corrected                              |
| flux_lya_err   | Uncertainty in flux_lya                                                         |
| flux_oii       | [O II] flux: flux_aper if flag_aper=1, else pipeline flux (same units)         |
| flux_oii_err   | Uncertainty in flux_oii                                                         |
| sn             | S/N for line emission; -999 for continuum sources                               |
| det_type       | Detection type: 'line' or 'cont'                                                |
| apcor          | Aperture correction applied at 4500 Ang                                         |
| p_conf         | RF classifier LAE confidence (1=high, 0=low)                                    |
| p_cnn          | CNN classifier LAE/faint-OII confidence (1=high, 0=low)                         |

Bad values: -999.0 for floats, 'n/a' for strings.

### HPSC2 Spectra File: hetdex_sc2_spec_vX.X.fits (Table 7 in PDR1 paper)

| HDU          | Type        | Dimensions             | Description                                         |
|--------------|-------------|------------------------|-----------------------------------------------------|
| 0:PRIMARY    | PrimaryHDU  | --                     | Empty                                               |
| 1:INFO       | BinTableHDU | 7367R x 27C            | Copy of main HPSC2 catalog                          |
| 2:SPEC       | ImageHDU    | (1036 x 1,107,763)     | PSF-weighted, aperture+extinction-corrected 1D spectra in 10^-17 erg/s/cm^2/Ang |
| 3:SPEC_ERR   | ImageHDU    | (1036 x 1,107,763)     | Uncertainty in SPEC                                 |
| 4:WAVELENGTH | ImageHDU    | (1036,)                | Wavelength array 3470-5540 Ang in 2 Ang steps        |

Row index in SPEC/SPEC_ERR matches row index in INFO.

### Supplemental Detection Info Table: hetdex_sc2_detinfo_vX.X.fits / .dat

Contains every quality-controlled emission-line and continuum detection, including
all low-confidence LAE candidates (p_conf < 0.5, p_cnn < 0.5). Useful for:
- Tracing sources back to individual detections via `selected_det == True`
- Accessing line-fit parameters: `wave`, `sigma`, `chi2`, `continuum`
- ELiXer outputs: `plya_classification`, `z_elixer`
- Diagnose outputs: `z_diagnose`, `cls_diagnose`
- Friends-of-Friends cluster info: `wave_group_*`
- Imaging counterpart info: `ra_aper`, `dec_aper`, `major`, `minor`, `theta`

---

## 8. Notebook Curriculum Map

Notebooks are in `pdr_dir/software/dexcube/notebooks/` on the JupyterHub, or in
`notebooks/` after cloning https://github.com/HETDEX/dexcube. Run sequentially.

| # | File                                   | Key inputs             | Key outputs              | Science goal                           |
|---|----------------------------------------|------------------------|--------------------------|----------------------------------------|
| 01| 01-DataModel+IFU-Index.ipynb           | ifu-index.fits         | --                       | Data model overview, IFU index         |
| 02| 02-DownloadingCubes.ipynb              | ifu-index, wget        | Local FITS cubes         | Remote download workflow               |
| 03| 03-DataCubeFormat.ipynb                | Local FITS cube        | --                       | HDU structure, units, WCS              |
| 04| 04-MaskingOptions.ipynb                | Local FITS cube        | Boolean mask arrays      | Build quality masks from MASK HDU      |
| 05| 05-CubeWidget.ipynb                    | Local FITS cube        | --                       | Interactive xylambda cube browser     |
| 06| 06-CoordinateQuery.ipynb               | ifu-index, RA/Dec      | List of covering cubes   | Find cubes by sky coordinate           |
| 07| 07-CollapsingCubes.ipynb               | Local FITS cube        | 2D FITS image            | Narrow-band / white-light images       |
| 08| 08-ExtractingSpectra.ipynb             | Local FITS cube        | 1D spectrum (FITS/ECSV)  | Circular aperture spectral extraction  |
| 09| 09-CatalogExtractions.ipynb            | Source catalog, cubes  | Astropy Table            | Batch extraction over source list      |
| 10| 10-HETDEX-Source-Catalog.ipynb         | HPSC2 catalog          | --                       | Catalog structure, cross-matching      |
| 11| 11-Source-Look-Up.ipynb                | HPSC2, cubes           | --                       | Coordinate/ID to cube look-up         |
| 12| 12-BatchDownloads-ForRemoteUsers.ipynb | ifu-index, wget        | Local cube archive       | Efficient bulk download                |

### Science Workflow Quick Reference

| Science goal                                             | Notebooks            |
|----------------------------------------------------------|----------------------|
| Inspect a single datacube interactively                  | 01 -> 03 -> 05       |
| Extract a 1D spectrum at a known RA/Dec                  | 01 -> 06 -> 08       |
| Build a narrow-band line flux map                        | 01 -> 06 -> 04 -> 07 |
| Cross-match a source list to HETDEX detections           | 10 -> 11             |
| Batch-extract spectra for a science sample               | 01 -> 06 -> 08 -> 09 |
| Download cubes for offline analysis                      | 01 -> 02 -> 12       |
| Find LAEs in a field                                     | 10 -> 11 -> 06 -> 08 |

---

## 9. Access & Data Products

### JupyterHub (recommended -- data pre-mounted, no download needed)

1. Create TACC account: https://accounts.tacc.utexas.edu/register
2. Request HETDEX access: https://tacc.utexas.edu/portal/login?next=/tacc-user-portal/hetdex-access-request/
3. Sign in to hub: https://jupyter.tacc.cloud
4. Clone notebooks: `git clone https://github.com/HETDEX/dexcube.git`

No persistent storage is offered to public users. Download your outputs before
closing the server session.

### Remote Download (data is publicly accessible, no account required)

```bash
# Download a single cube
wget https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/datacubes/20190405020/dex_cube_20190405020_034.fits

# Batch download with directory structure preserved
wget --cut-dirs=4 -nH -x {url}
```

See Notebooks 02 and 12 for batch download examples including parallel options.

### Docker (self-contained environment, no TACC account needed)

```bash
docker run --pull always -p 8888:8888 \
  -v "$PWD":/home/jovyan/work \
  hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token='' \
  --ServerApp.root_dir=/home/jovyan \
  --ServerApp.default_url=/lab/tree/work/README.md
```

Inside Docker: `pdr_dir = '/home/jovyan/work/pdr1/'`

### Available Data Files at PDR1 Base URL

| File                                | Size    | Description                                       |
|-------------------------------------|---------|---------------------------------------------------|
| ifu-index.fits / .h5 / .txt         | <200 MB | Master IFU manifest                               |
| hetdex_sc2_vX.X.fits / .dat         | 11 GB   | HPSC2 main source catalog                         |
| hetdex_sc2_spec_vX.X.fits           | 11 GB   | HPSC2 1D spectra for all sources                  |
| hetdex_sc2_detinfo_vX.X.fits / .dat | 11 GB   | Supplemental detection information table          |
| datacubes/SHOTID/*.fits             | 7.4 TB  | 431,713 IFU datacubes (~19 MB each)               |
| detect/detect_hdrX.h5               | 1.7 TB  | Raw emission-line detection databases             |
| detect/cont_hdrX.h5                 | 1.7 TB  | Raw continuum detection databases                 |
| detect/elixer/NNNNN/*.jpg           | 587 GB  | ELiXer diagnostic reports (~150 KB each)          |

**ELiXer reports** URL pattern:
`https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/detect/elixer/{first5digits}/{detectid}.jpg`

---

## 10. Data Caveats and Limitations

### Early Data (2017)
Shotids beginning with `2017` correspond to early survey data when VIRUS operated
with fewer than 20 IFUs. About half the amplifiers were flagged bad; detectors had
significant pox and charge traps. Avoid for LAE science without manual inspection.

### Local Sky Subtraction
PDR1 uses local sky subtraction optimized for detecting faint emission lines.
- **Not suitable** for absolute surface-brightness measurements or intensity mapping
- **Not suitable** for studies of very extended nearby galaxies (scales comparable
  to the 52" x 52" IFU field of view may show over-subtraction)
- Flux measurements near bright or extended sources may be affected

### Flux Sensitivity
Survey reaches ~50% completeness at 1.1 x 10^-16 erg/s/cm^2 (wavelength and
seeing dependent). Sensitivity is lower at the blue end (< 4700 Ang). PDR1 is not
suited for direct luminosity function measurements without completeness corrections.

### Source Detection on Datacubes
Source detection was performed on internal fiber data, not on interpolated cubes.
Independent detection on PDR1 cubes recovers median S/N = 0.75 +/- 0.23 relative
to catalog values (due to correlated noise from spatial interpolation onto 0.5"
grid). The BADDET bitmask (8192) masks cube locations of catalog-rejected detections.

### Spectral Stacking
Sky residuals (~1% of sky level per spectrum) accumulate in stacks. Published
HETDEX stacking analyses subtract a correction spectrum derived from 200 random sky
apertures per field -- this correction is NOT included in the PDR1 datacubes.

### Spectral Extraction: Cube vs. Pipeline
Circular aperture spectra from cubes agree with internal pipeline to ~5-10% (blue
end shows the largest difference). Standard aperture in PDR1 examples: r = 3.5" circle.

---

## 11. Software Environment

### Python Requirements
- Python 3.10+
- See `requirements.txt` in dexcube repo for full pinned package list

### Key Packages and Roles

| Package    | Role                                                              |
|------------|-------------------------------------------------------------------|
| astropy    | FITS I/O, WCS, coordinates, tables, units                         |
| numpy      | Array operations on cube data                                     |
| matplotlib | Static plots, spectra, images                                     |
| ipywidgets | CubeWidget interactive slicing (Notebook 05)                      |
| scipy      | Linear interpolation used in cube generation (griddata)           |
| tables     | PyTables for HDF5 access to raw detection databases               |
| h5py       | Alternative HDF5 access                                           |

### Jupyter Environment Notes

- Use **JupyterLab** (not classic Notebook) for full widget support
- Use `%matplotlib widget` (not `%matplotlib inline`) for CubeWidget and
  interactive plots
- ipywidgets lab extension:
  `jupyter labextension install @jupyter-widgets/jupyterlab-manager`
- On the public JupyterHub: no persistent storage; download outputs before session ends

---

## 12. Common Errors and Gotchas

| Symptom                                      | Cause                                        | Fix                                                      |
|----------------------------------------------|----------------------------------------------|----------------------------------------------------------|
| CubeWidget shows static image only           | Wrong matplotlib backend                     | Use `%matplotlib widget`                                 |
| FileNotFoundError opening cube               | Wrong pdr_dir for your environment           | Set pdr_dir per Section 2 for your access method         |
| WCS gives wrong sky coordinates              | Using naxis=3 for spatial query              | `wcs2d = WCS(header, naxis=2)` for spatial-only WCS      |
| Flux seems factor of 2 too large             | Treating per-bin as per-Ang                  | Divide DATA by 2.0 to get erg/s/cm^2/Ang                 |
| Flux seems factor ~1e17 too large            | Units not applied                            | DATA is in 10^-17 units; multiply by 1e-17 for CGS       |
| Noisy spectra at blue end                    | Low throughput at wavelength edges           | Restrict science analysis to 3600-5400 Ang               |
| Stacked spectra have residual sky bumps      | Sky correction not in cubes                  | Subtract correction from ~200 random sky apertures       |
| Cube orientation not north-up                | Cubes aligned to HET PA, not sky N           | Always use WCS headers for coordinates                   |
| NaN values in cube                           | Spaxel outside valid fiber region            | Expected behaviour at cube spatial edges                 |
| Low S/N on faint sources vs. catalog         | Correlated noise from spatial interpolation  | Expect ~75% of catalog S/N; use BADDET mask for searches |
| 2017 data looks noisy/artifact-rich          | Early survey, few IFUs, bad amps and detectors| Avoid 2017 data for LAE science                         |
| flag=1 in ifu-index means GOOD               | Opposite convention from MASK HDU bitmask    | ifu-index: flag=1=good. MASK HDU bitmask: 0=good.        |
| Source appears multiple times in HPSC2       | Multiple observations of same object         | Same source_name, different source_id per observation    |
| flux=-999 for source in catalog              | Continuum source with no measured line flux  | Use flux_lya or flux_oii columns instead                 |

---

## 13. Key References

- **PDR1 paper**: Mentuch Cooper et al. 2026, "HETDEX Public Data Release 1:
  Source Catalog 2 and Datacubes from ~90 deg^2 of Integral-Field Optical
  Spectroscopy" (submitted to ApJ). This context file is derived from this paper.
- **HPSC2 Zenodo**: doi:10.5281/zenodo.19581262
  https://doi.org/10.5281/zenodo.19581262
- **HETDEX Survey Design**: Gebhardt et al. 2021, ApJ 923, 217
  doi:10.3847/1538-4357/ac2e03 | https://arxiv.org/abs/2110.04298
- **HETDEX Instrumentation (VIRUS)**: Hill et al. 2021, AJ 162, 298
  doi:10.3847/1538-3881/ac2c02 | https://arxiv.org/abs/2110.03843
- **HETDEX Source Catalog 1 (HPSC1)**: Mentuch Cooper et al. 2023, ApJ 943, 177
  doi:10.3847/1538-4357/aca962 | https://arxiv.org/abs/2301.01826
- **HETDEX AGN Catalog 1**: Liu et al. 2022, ApJS 261, 24
  doi:10.3847/1538-4365/ac6ba6 | https://arxiv.org/abs/2204.13658
- **HETDEX AGN Catalog 2**: Liu et al. 2025, ApJS 276, 72
  doi:10.3847/1538-4365/ada4a5
- **ELiXer (detection/classification tool)**: Davis et al. 2023a, ApJ 946, 86
  doi:10.3847/1538-4357/acb0ca | https://github.com/HETDEX/elixer
- **Diagnose (spectral classification)**: Debski & Zeimann 2024, ASCL 2411.020
  https://github.com/grzeimann/Diagnose
- **HETDEX-LOFAR Catalog**: Debski et al. 2025, ApJ 978, 101
  doi:10.3847/1538-4357/ad957b
- **HETDEX-DESI VAC**: Landriau et al. 2025, ApJ 995, 220
  doi:10.3847/1538-4357/ae1ae6
- **HETDEX-GAIA Star Catalog**: Hawkins et al. 2021, ApJ 911, 108
  doi:10.3847/1538-4357/abe9bd
- **LAE Surface Brightness Profiles**: Mentuch Cooper et al. 2026, ApJ 1000, 38
  doi:10.3847/1538-4357/ae44f3
- **CNN LAE Classifier**: Mukae et al. 2026, ApJ (in press)
- **Dark Energy Explorers (citizen science)**: House et al. 2023, ApJ 950, 82
  doi:10.3847/1538-4357/accdd0
  https://www.zooniverse.org/projects/erinmc/dark-energy-explorers
- **Lya Intensity Mapping**: Lujan Niemeyer et al. 2026, ApJ 999, 177
  doi:10.3847/1538-4357/ae3a98

### Citation Requirements

Papers using HETDEX PDR1 data must cite:
- HET telescope: Ramsey et al. 1998
- VIRUS instrument: Hill et al. 2021
- HETDEX survey: Gebhardt et al. 2021
Plus acknowledgments as specified at https://hetdex.org/papers/

---

## 14. Contact & Support

- **Data questions**: Erin Mentuch Cooper -- erin.hetdex@gmail.com
- **Bug reports / notebook issues**: https://github.com/HETDEX/dexcube/issues
- **HETDEX website**: https://hetdex.org
- **Data portal**: https://hetdex.org/data-results/
- **JupyterHub**: https://jupyter.tacc.cloud
- **TACC account registration**: https://accounts.tacc.utexas.edu/register
