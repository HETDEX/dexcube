# HETDEX_CONTEXT.md
# Machine-readable context for LLM-assisted scientific analysis of HETDEX PDR1
# Reference paper: Mentuch Cooper et al. 2026 — "HETDEX Public Data Release 1"
# Notebooks: https://github.com/HETDEX/dexcube
# Maintained by: Erin Mentuch Cooper (erin.hetdex@gmail.com)
# Last updated: 2026-04-22

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
- **Wavelength coverage**: 3470-5540 Ang (observed frame, in air)
- **Spectral resolution**: R ~ 750-950 (FWHM ~ 4.7-5.6 Ang); median R ~ 800
- **Spectral sampling**: 2 Ang per pixel
- **Median image quality**: FWHM ~ 1.8 arcsec
- **Exposure time per field**: ~1200 s total (3 dithered exposures of 6-7 min each)
- **Survey dates**: Science verification January 2017; main survey Dec 2017 - Jul 2024
- **Total survey footprint**: ~540 deg^2 (Spring + Fall fields)
- **PDR1 sky coverage**: 86.67 deg^2 non-contiguous across 431,713 IFU datacubes

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

### Wavelength Notes

- All spectral data are in **air** wavelengths.
- Redshifts include air-to-vacuum conversion and barycentric velocity correction.
- Rest-frame vacuum wavelength of Lya: 1215.67 Ang
- Rest-frame air wavelength of [O II] doublet: 3727.8 Ang

---

## 2. Public Data Release 1 (PDR1)

PDR1 covers all science-quality HETDEX observations 2017-01-01 to 2024-07-31.

- **Number of IFU datacubes**: 431,713
- **Number of observations (shotids)**: 6,778
- **Total data volume**: ~9.8 TB (datacubes: 7.4 TB; raw detections: 1.7 TB)
- **Each cube size**: ~19 MB
- **PDR1 base URL**: http://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/
- **Catalog URL**: http://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/hetdex_source_catalog_2/
- **HPSC2 Zenodo DOI**: https://doi.org/10.5281/zenodo.19581262

### STARTUP BOOTSTRAP — Run This First in Every Session

**Before any analysis code, always run this complete block.** It sets `pdr_dir`,
creates the directory if needed, and downloads `ifu-index.fits` if missing.
On the HETDEX JupyterHub the data is pre-mounted and nothing is downloaded.
On Docker or any remote/local environment the index file is fetched automatically.

```python
import os
import os.path as op
import subprocess
import numpy as np
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS

# --- 1. Set pdr_dir for this environment ---
pdr_dir = '/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/'
if not op.exists(pdr_dir):
    # Docker container or local download path
    pdr_dir = '/home/jovyan/work/pdr1/'

# --- 2. Create directory if it doesn't exist ---
os.makedirs(pdr_dir, exist_ok=True)

# --- 3. Download ifu-index.fits if not already present ---
ifu_index_path = op.join(pdr_dir, 'ifu-index.fits')
if not op.exists(ifu_index_path):
    print("ifu-index.fits not found. Downloading...")
    url = "http://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/ifu-index.fits"
    subprocess.run(["wget", "--quiet", "-O", ifu_index_path, url], check=True)
    print(f"Downloaded to: {ifu_index_path}")
else:
    print(f"ifu-index.fits found at: {ifu_index_path}")

# --- 4. Load the IFU index and build coordinate array ---
ifu_data   = Table.read(ifu_index_path)
ifu_coords = SkyCoord(ra=ifu_data['ra_cen']*u.deg,
                      dec=ifu_data['dec_cen']*u.deg)

print(f"pdr_dir  : {pdr_dir}")
print(f"IFU rows : {len(ifu_data):,}")
```

After running this block you have `pdr_dir`, `ifu_data`, and `ifu_coords`
available for all subsequent operations.

### Data Path by Environment

| Environment | pdr_dir |
|-------------|---------|
| HETDEX JupyterHub (https://jupyter.tacc.cloud) | `/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/` |
| TACC Stockyard | `/corral-repl/utexas/Hobby-Eberly-Telesco/public/HETDEX/pdr/pdr1/` |
| Docker container (hetdex/dexcube) | `/home/jovyan/work/pdr1/` |

### File Path Convention for Datacubes

```python
datacube_path = op.join(pdr_dir, 'datacubes', str(shotid),
                        'dex_cube_{}_{}.fits'.format(shotid, ifuslot))
# Example: pdr1/datacubes/20190405020/dex_cube_20190405020_034.fits
```

### Downloading Datacubes (Notebook 02)

```python
import os, subprocess
from urllib.parse import urlsplit

# Download a single cube
base_url = "http://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/datacubes"
shotid = 20190405020
ifuslot = '034'
url = f"{base_url}/{shotid}/dex_cube_{shotid}_{ifuslot}.fits"

base_url_path = '/hetdex/HETDEX/pdr/pdr1/'
rel_path = urlsplit(url).path.split(base_url_path, 1)[-1]
local_path = os.path.join(pdr_dir, rel_path)
os.makedirs(os.path.dirname(local_path), exist_ok=True)
if not op.exists(local_path):
    subprocess.run(['wget', '-q', '-O', local_path, url])
    print(f"Downloaded: {rel_path}")
else:
    print(f"Already exists: {local_path}")
```

```bash
# Batch download from urls.txt (terminal)
wget --cut-dirs=4 -nH -x -i urls.txt

# Parallel download (4 workers — don't use too many)
cat urls.txt | xargs -n 1 -P 4 wget --cut-dirs=4 -nH -x
```

---

## 3. Datacube Format

ADR (atmospheric differential refraction) **is corrected** during cube generation
— the public cubes have ADR applied per wavelength slice. Do not correct again.

### FITS HDU Structure (Table 2 in PDR1 paper)

| HDU | EXTNAME | Description                                                    | Shape          |
|-----|---------|----------------------------------------------------------------|----------------|
| 0   | PRIMARY | Empty header                                                   | None           |
| 1   | DATA    | Flux in 10^-17 erg/s/cm^2 per 2 Ang spectral bin             | (1036, 104, 104) |
| 2   | ERROR   | 1-sigma uncertainty (same units as DATA)                       | (1036, 104, 104) |
| 3   | MASK    | Bitmask quality flags per spaxel                               | (1036, 104, 104) |

**All cubes have fixed dimensions: (1036, 104, 104)** — wavelength x y x in numpy.

### Opening a Cube (Notebook 03)

```python
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

hdul = fits.open(datacube_path)
flux   = hdul["DATA"].data   # shape (1036, 104, 104)
error  = hdul["ERROR"].data
mask   = hdul["MASK"].data
header = hdul["DATA"].header
wcs    = WCS(header)
hdul.close()
```

### Units

- **DATA**: 10^-17 erg s^-1 cm^-2 per **2 Ang bin** (NOT per Ang)
  - Divide by 2.0 for flux density in erg/s/cm^2/Ang
  - Multiply by 1e-17 for CGS
- **ERROR**: same units as DATA (1-sigma per spaxel per 2 Ang bin)
- Spaxels outside valid fiber region = **NaN**

### Dimensions

- Wavelength axis (numpy axis 0): 1036 pixels, 3470-5540 Ang in 2 Ang steps
- Spatial axes (numpy axes 1, 2): 104 x 104 spaxels at 0.5 arcsec/spaxel = 52" x 52"

### Wavelength Array

```python
# From linspace (used in notebooks)
wave = np.linspace(3470, 5540, num=1036)

# From WCS
wcs_spectral = WCS(header).sub(['spectral'])
wavelengths = wcs_spectral.pixel_to_world(np.arange(flux.shape[0]))

# Wavelength at pixel index z_index
wavelength_angstrom = wcs.wcs_pix2world(0, 0, z_index, 0)[2]
```

### WCS and Spatial Coordinates (Notebook 06)

```python
from astropy.coordinates import SkyCoord
import astropy.units as u

# Always use celestial WCS for spatial operations
wcs_celestial = WCS(header).celestial

# Convert sky coord to pixel
x_pix, y_pix = wcs_celestial.world_to_pixel(coord)

# Check exact coverage
inside = wcs_celestial.footprint_contains(coord)

# Pixel scale
pixel_scale = np.abs(wcs.proj_plane_pixel_scales()[0]).to(u.arcsec).value
# OR
from astropy.wcs.utils import proj_plane_pixel_scales
pixel_scale_arcsec = proj_plane_pixel_scales(wcs.celestial)[0] * 3600  # deg->arcsec
```

**Cubes are NOT north-up.** Aligned to HET tracker angle. Always use WCS.

---

## 4. Bitmask Definitions (Table 3 in PDR1 paper)

**Convention: 0 = GOOD. Non-zero = flagged.**
This is OPPOSITE of `flag` in ifu-index.fits where flag=1=good, flag=0=bad.

| Integer | Name       | Description                              | Recommended |
|---------|------------|------------------------------------------|-------------|
| 0       | Good       | No flag — data is usable                 | --          |
| 1       | MAIN       | Flagged in reduction (calfibe==0.0)      | Always mask |
| 2       | FTF        | Fiber-to-fiber deviation > 0.5           | Always mask |
| 4       | CHI2FIB    | chi2fib > 150 (poor fiber profile fit)   | Always mask |
| 8       | BADPIX     | Bad pixel region                         | Always mask |
| 16      | BADAMP     | Bad amplifier                            | Always mask |
| 32      | LARGEGAL   | Within large galaxy or PN mask           | Optional    |
| 64      | METEOR     | Known meteor track                       | Always mask |
| 128     | BADSHOT    | Bad shot (not present in PDR1)           | N/A         |
| 256     | THROUGHPUT | Throughput < 0.08 (not present in PDR1)  | N/A         |
| 512     | BADFIB     | Known bad fiber                          | Always mask |
| 1024    | SAT        | Satellite track                          | Recommended |
| 2048    | BADCAL     | Sky/calibration issue at wavelength      | Optional    |
| 4096    | PIXMASK    | Native spectrum counts == 0              | Always mask |
| 8192    | BADDET     | ML-flagged detection (5x5x5 px mask)     | For searches|

### Masking Patterns (Notebook 04)

```python
# Minimum mask — always apply
good = (mask & (1 | 2 | 4 | 8 | 16)) == 0

# Full mask for emission-line searches
good = mask == 0

# Apply mask to flux cube (fill with NaN)
flux[np.where(mask > 0)] = np.nan

# Apply mask but keep BADCAL (e.g. to recover line at 3640 Ang)
good_mask_values = (mask == 0) | (mask == 2048)
data_mask = (~good_mask_values) | (flux == 0)
flux[data_mask] = np.nan

# Isolate only meteor-flagged pixels
meteor_mask = (mask_slice & 64) != 0
flux_meteor = np.where(meteor_mask, flux_slice, np.nan)

# Find IFUs with meteor coverage from ifu-index
met_indices = np.where(ifu_data['flag_meteor'] < 0.5)[0]
```

### BADCAL Flagged Spectral Windows

- 3534-3556 Ang: sky line, masked in every observation
- 5194-5197 Ang and 5200-5205 Ang: sky feature (amplifier/shot-dependent)
- 5456-5466 Ang: sky line (amplifier/shot-dependent)

BADCAL can be ignored for bright sources: stars, nearby galaxies, most AGN.

---

## 5. IFU Index File (Notebook 01)

The IFU index is the master look-up table for all datacubes.

```python
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

ifu_data = Table.read(op.join(pdr_dir, 'ifu-index.fits'))

# Build SkyCoord array of all IFU centers (used in all coordinate queries)
ifu_coords = SkyCoord(ra=ifu_data['ra_cen']*u.deg,
                      dec=ifu_data['dec_cen']*u.deg)
```

### Key Columns (Table 6 in PDR1 paper)

| Column         | Type    | Units  | Description                                            |
|----------------|---------|--------|--------------------------------------------------------|
| shotid         | int64   | --     | Observation ID integer (YYYYMMDDNNN)                   |
| ifuslot        | str     | --     | IFU slot identifier (e.g., '046', '063')               |
| ra_cen         | float32 | deg    | RA of IFU center (ICRS J2000)                          |
| dec_cen        | float32 | deg    | Dec of IFU center (ICRS J2000)                         |
| flag           | float32 | --     | **1=fully useable, 0=fully flagged** (1=GOOD!)         |
| flag_badamp    | float32 | --     | Fraction unaffected by bad amplifier(s)                |
| flag_badfib    | float32 | --     | Fraction unaffected by bad fiber(s)                    |
| flag_meteor    | float32 | --     | Fraction unaffected by meteor trail                    |
| flag_satellite | float32 | --     | Fraction unaffected by satellite trail                 |
| flag_shot      | float32 | --     | Fraction unaffected by shot-level flagging             |
| flag_throughput| float32 | --     | Fraction unaffected by low throughput                  |
| field          | str     | --     | 'dex-spring', 'dex-fall', 'cosmos', 'goods-n', etc.   |
| fwhm_virus     | float32 | arcsec | Seeing FWHM from VIRUS                                 |
| response_4540  | float32 | --     | Normalised system throughput at 4540 Ang               |
| mjd            | float32 | days   | Modified Julian Date                                   |
| exptime        | float32 | s      | Exposure time                                          |
| pa             | float64 | deg    | HET tracker rotation angle                             |
| fluxlimit_4600 | float32 | --     | Flux limit at 4600 Ang                                 |

Also present: ra_shot, dec_shot, n_ifu, datevobs, ambtemp, dewpoint,
humidity, pressure, structaz, time, trajcdec, trajcpa, trajcra.

PDR1 flag statistics: 91.6% of cubes fully unflagged; 7.8% flagged for bad
amplifiers, 0.2% bad fibers, 0.12% satellites, 0.04% meteors.

---

## 6. Coordinate Queries (Notebook 06)

### Single coordinate search

```python
# Example: Lyman Alpha Blob at z=2.53
coord = SkyCoord(ra=228.78581*u.deg, dec=51.268036*u.deg)

# Find IFUs within 37 arcsec (IFU radius ~26 arcsec)
sel = coord.separation(ifu_coords) < 37*u.arcsec

# Get paths to matching cubes
for row in ifu_data[sel]:
    shotid  = row['shotid']
    ifuslot = row['ifuslot']
    datacube_path = op.join(pdr_dir, 'datacubes', str(shotid),
                            'dex_cube_{}_{}.fits'.format(shotid, ifuslot))
    print(datacube_path)

    # Verify exact WCS coverage
    with fits.open(datacube_path, memmap=False) as hdul:
        w = WCS(hdul['DATA'].header).celestial
        inside = w.footprint_contains(coord)
        print(inside)
```

### Catalog cross-match (many coordinates at once)

```python
from astropy.table import hstack, unique

catalog_coords = SkyCoord(ra=catalog['ra'], dec=catalog['dec'], unit='deg')

# All IFU/source pairs within search radius
idx_ifu, idx_catalog, d2d, d3d = catalog_coords.search_around_sky(
    ifu_coords, 37*u.arcsec)

# Build matched table
table = hstack([catalog_coords[idx_catalog], catalog[idx_catalog],
                ifu_data[idx_ifu]])
table.rename_column('col0', 'coords')

# Unique IFU list for downloading
ifulist = unique(table['shotid', 'ifuslot'])
ifu_pairs = [(int(row['shotid']), str(row['ifuslot'])) for row in ifulist]

# Build URL list
base_url = "http://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/datacubes"
urls = []
with open("urls.txt", "w") as f:
    for shotid, ifuslot in ifu_pairs:
        url = f"{base_url}/{shotid}/dex_cube_{shotid}_{ifuslot}.fits"
        urls.append(url)
        f.write(url + "\n")
print(f"Number of cubes: {len(urls)}, approx {len(urls)*0.027:.2f} Gb")
```

---

## 7. Collapsing Cubes to Images (Notebook 07)

```python
wave = np.linspace(3470, 5540, num=1036)

# Apply mask before collapsing
flux[np.where(mask > 0)] = np.nan

# Narrowband image at known wavelength (e.g. Lya at z=2.53)
wave_src = 4295.9  # Ang
z_index = np.abs(wave_src - wave) < 10
flux_nb    = np.nansum(flux[z_index, :, :], axis=0)
error_nb   = np.sqrt(np.nansum(error[z_index, :, :]**2, axis=0))

# Broadband continuum (3800-5200 Ang)
z_index_cont = (wave >= 3800) & (wave <= 5200)
flux_cont = np.nansum(flux[z_index_cont, :, :], axis=0)

# Continuum-subtracted line map
dwave = 10
dw_nb   = 2 * dwave
dw_cont = 5200 - 3800
flux_cont_sub = dw_nb * (flux_cont / dw_cont)
line_map = flux_nb - flux_cont_sub

# RGB composite for multi-line galaxy (e.g. z=0.067)
redshift = 0.067
waveoii  = 3727.8
waveoiii = 5008.24
z_oii  = np.abs(waveoii*(1 + redshift) - wave) < 10
z_oiii = np.abs(waveoiii*(1 + redshift) - wave) < 10
red   = np.nansum(flux[z_oii,  :, :], axis=0) - flux_cont_sub
green = np.nansum(flux[z_oiii, :, :], axis=0) - flux_cont_sub
blue  = flux_cont

# Convert pixel center for zoomed plots
x_center, y_center = wcs.celestial.world_to_pixel(coord)
pix_scale = np.abs(wcs.wcs.cdelt[0]) * 3600  # deg->arcsec
half_width_pix = zoom_radius_arcsec / pix_scale
```

---

## 8. Spectral Extraction (Notebook 08)

### Simple circular aperture

```python
r_arcsec = 2.0

# Get pixel centre
x_pix, y_pix = wcs.celestial.world_to_pixel(coord)
x_pix, y_pix = float(x_pix), float(y_pix)
pixel_scale   = np.abs(wcs.proj_plane_pixel_scales()[0]).to(u.arcsec).value
r_pix = r_arcsec / pixel_scale

# Boolean aperture mask
ny, nx = flux.shape[1:]
yy, xx = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
ap_mask = (xx - x_pix)**2 + (yy - y_pix)**2 <= r_pix**2

# Apply data mask first
data_mask = np.where((mask > 0) | (flux == 0))
flux[data_mask] = np.nan

# Sum within aperture
spectrum = np.nansum(flux[:, ap_mask], axis=1)
spectrum[spectrum == 0] = np.nan

# Wavelengths from WCS
wcs_spectral = WCS(header).sub(['spectral'])
wavelengths = wcs_spectral.pixel_to_world(np.arange(flux.shape[0])).to(u.Angstrom)
```

### Aperture-corrected extraction with photutils (recommended, r=3.5 arcsec standard)

```python
from photutils.aperture import CircularAperture

r_arcsec = 3.5
r_pix    = r_arcsec / pixel_scale

ap     = CircularAperture((x_pix, y_pix), r=r_pix)
apmask = ap.to_mask(method='exact')
if isinstance(apmask, list):
    apmask = apmask[0]

W     = apmask.to_image((ny, nx))  # fractional weights [0-1]
A_tot = W.sum()

# Wavelength-dependent aperture correction for missing fiber coverage
spectrum = np.zeros(flux.shape[0])
for i in range(flux.shape[0]):
    slice_flux = flux[i]
    valid      = np.isfinite(slice_flux)
    A_valid    = (W * valid).sum()
    if A_valid > 0:
        spectrum[i] = np.nansum(slice_flux * W) * (A_tot / A_valid)
    else:
        spectrum[i] = np.nan
```

### Built-in get_spectra function (Notebooks 09 and 11)

```python
from dexcube.get_spec import get_spectra

# Basic usage (returns spectrum, error, aperture correction array)
spec, err, apcor = get_spectra(coord, shotid, ifuslot, data_dir=pdr_dir)

# With wavelength returned
spec, err, apcor, wave = get_spectra(
    coord, shotid, ifuslot, pdr_dir,
    radius=3.5,
    return_wave=True
)

# Keep SAT-flagged data but mask everything else
spec, err, ap = get_spectra(coord, shotid, ifuslot, pdr_dir,
                             include_only_bits="SAT")

# Mask all nonzero bits but allow BADCAL through
spec, err, ap = get_spectra(coord, shotid, ifuslot, data_dir=pdr_dir,
                             exclude_bits="ALL_NONZERO",
                             keep_bits="BADCAL")

# No masking at all (compare to pipeline spectrum)
spec, err, ap, wave = get_spectra(
    coord, shotid, ifuslot, pdr_dir,
    radius=3.5, exclude_bits=None, include_only_bits=None,
    return_wave=True)

# Returns None if coord is not in cube footprint — always check
if spec is None:
    print("Coordinate not covered by this cube")
```

---

## 9. Batch Catalog Extractions (Notebook 09)

```python
from dexcube.get_spec import get_spectra
from multiprocessing import Pool
import time
from astropy.table import Column

# Wrapper for parallel processing
def process_row(row):
    return get_spectra(row['coords'], row['shotid'], row['ifuslot'],
                       data_dir=pdr_dir)

# Run in parallel (20 workers typical on JupyterHub)
t0 = time.time()
with Pool(processes=20) as pool:
    results = pool.map(process_row, table)
print('Done in {:3.2f} min.'.format((time.time()-t0)/60))

# Store results back into astropy Table
nan_array = np.full(1036, np.nan, dtype=np.float32)
num_rows = len(table)
table.add_column(Column(np.tile(nan_array, (num_rows, 1)), name='spectrum'))
table.add_column(Column(np.tile(nan_array, (num_rows, 1)), name='error'))
table.add_column(Column(np.tile(nan_array, (num_rows, 1)), name='apcor'))

for i, row in enumerate(table):
    if results[i] is not None:
        table['spectrum'][i], table['error'][i], table['apcor'][i] = results[i]

table.remove_column('coords')  # SkyCoord column can't be saved to FITS
table.write('output_spectra.fits', overwrite=True)
```

---

## 10. Source Populations (HPSC2)

PDR1 includes the **HETDEX Public Source Catalog 2 (HPSC2)**. The recommended
quality cut for robust science samples is p_conf >= 0.5 AND p_cnn >= 0.5.

### Source Counts by Type (full PDR1 total)

| source_type | Count     | Redshift range  | Primary line/method                  |
|-------------|-----------|-----------------|--------------------------------------|
| lae         | 426,654   | 1.88 < z < 3.52 | Lya 1215.67 Ang (vacuum)             |
| oii         | 491,411   | 0 < z < 0.48    | [O II] 3727.8 Ang doublet            |
| agn         | 18,303    | 0 < z < 4.6     | Broad lines / AGN catalog Liu+2025   |
| lzg         | 19,457    | 0 < z < 0.5     | Continuum template (no emission)     |
| star        | 150,608   | z = 0           | Stellar templates (Diagnose)         |
| **total**   | **1,085,129** |             |                                      |

Full LAE candidate sample (before p_conf/p_cnn cuts): 1,632,604.

---

## 11. HPSC2 Catalog Access (Notebook 10)

```python
from astropy.io import fits
from astropy.table import Table
import numpy as np

path_to_cat = op.join(pdr_dir, 'hetdex_source_catalog_2/')
version = 'v1.5'  # check directory for current version

# --- Main catalog (no spectra) ---
source_table = Table.read(op.join(path_to_cat,
                                   'hetdex_sc2_{}.fits'.format(version)))

# --- Catalog with spectra ---
hdu      = fits.open(op.join(path_to_cat,
                              'hetdex_sc2_spec_{}.fits'.format(version)))
spec      = hdu['SPEC'].data        # shape (1036, N_sources), 1e-17 erg/s/cm^2/Ang
spec_err  = hdu['SPEC_ERR'].data
wave_rect = hdu['WAVELENGTH'].data  # shape (1036,), Ang

# Access spectra for a selection
sel_lae  = source_table['source_type'] == 'lae'
sel_good = (source_table['p_conf'] >= 0.5) & (source_table['p_cnn'] >= 0.5)
sel_flux = source_table['flux_lya'] > 15
sel_date = source_table['shotid'] > 20240600000

sel = sel_lae & sel_good & sel_flux & sel_date
lae_spectra = spec[:, sel]   # shape (1036, N_selected)

# Coordinate search
from astropy.coordinates import SkyCoord
source_coords = SkyCoord(ra=source_table['RA'], dec=source_table['DEC'])
coord = SkyCoord(ra=220.21432*u.deg, dec=52.095898*u.deg)
sel_match = np.where(source_coords.separation(coord) < 1.*u.arcsec)[0]

# Plot spectrum for matched source
redshift = source_table['z_hetdex'][sel_match][0]
lya_wave = 1216 * (redshift + 1)
plt.plot(wave_rect, spec[:, sel_match[0]])
plt.xlim(lya_wave - 50, lya_wave + 50)

# --- Detection Info Table ---
det_table = Table.read(op.join(path_to_cat,
                                'hetdex_sc2_detinfo_{}.fits'.format(version)))
det_table.convert_bytestring_to_unicode()

# Example: find large resolved OII galaxies near IFU center
sel_oii     = (det_table['source_type'] == 'oii') & (det_table['major'] > 6)
sel_center  = (np.abs(det_table['x_ifu']) < 5) & (np.abs(det_table['y_ifu']) < 5)
sel_main    = (det_table['selected_det'] == True) & (det_table['n_members'] > 6)
sel = sel_oii & sel_center & sel_main
```

### Key Catalog Columns (Table 5 in PDR1 paper)

| Column         | Description                                                     |
|----------------|-----------------------------------------------------------------|
| source_name    | HETDEX IAU name (e.g. HETDEX J123449.19+511733.7)              |
| source_id      | Unique per observation (same source = same name, diff id)       |
| shotid         | Integer observation ID (YYYYMMDDNNN)                            |
| ifuslot        | IFU slot identifier string                                      |
| RA, DEC        | Source coordinates (ICRS J2000, degrees)                        |
| z_hetdex       | HETDEX spectroscopic redshift                                    |
| source_type    | 'lae', 'oii', 'agn', 'lzg', 'star'                            |
| flux_lya       | Lya flux (1e-17 erg/s/cm^2), extinction-corrected               |
| flux_oii       | [OII] flux (same units); flux_aper if flag_aper=1               |
| flag_aper      | 1=use flux_aper; 0=use PSF flux; -1=no OII                     |
| p_conf         | RF classifier LAE confidence (1=high, 0=low)                    |
| p_cnn          | CNN classifier LAE confidence (1=high, 0=low)                   |
| sn             | S/N for line emission; -999 for continuum                       |
| gmag           | HETDEX g magnitude                                              |
| detectid       | Representative detection ID                                     |
| field          | 'dex-spring', 'dex-fall', 'cosmos', 'goods-n', 'nep', 'ssa22' |

Bad values: -999.0 for floats, 'n/a' for strings.

---

## 12. Source Lookup and ELiXer Reports (Notebook 11)

```python
# Load subcube around a known source
size  = 10   # arcsec side of spatial cutout
wsize = 40   # Ang spectral width

nz, ny, nx = hdul['DATA'].shape
x_pix, y_pix = wcs.celestial.world_to_pixel(coord)
from astropy.wcs.utils import proj_plane_pixel_scales
pixel_scale_arcsec = proj_plane_pixel_scales(wcs.celestial)[0] * 3600
r_pix = size / pixel_scale_arcsec / 2

x_min = max(0, int(np.floor(x_pix - r_pix)))
x_max = min(nx, int(np.ceil(x_pix + r_pix)) + 1)
y_min = max(0, int(np.floor(y_pix - r_pix)))
y_max = min(ny, int(np.ceil(y_pix + r_pix)) + 1)
wslice = np.abs(wave - wave_src) < wsize/2

flux_cube  = hdul['DATA'].data[wslice, y_min:y_max, x_min:x_max].astype(float)
error_cube = hdul['ERROR'].data[wslice, y_min:y_max, x_min:x_max].astype(float)

# View ELiXer diagnostic report for a detection
from IPython.display import Image, display
det    = row['detectid']          # integer detectid
prefix = str(det)[:5]             # first 5 digits = directory
url    = f"https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/detect/elixer/{prefix}/{det}.jpg"
display(Image(url=url, width=900))
```

---

## 13. Raw Detection Databases (Notebook 11, Appendix A in PDR1 paper)

```python
import tables as tb

# Detection catalog files at pdr_dir/detect/
# detect_hdr3.h5: 2017-01-01 to 2021-08-31 (13,843,051 detections)
# detect_hdr4.h5: 2021-09-01 to 2023-08-31 (14,180,087 detections)
# detect_hdr5.h5: 2023-09-01 to 2024-07-31 (3,938,578 detections)
# detect_index_hdr5.h5: master index for all detections

# Open detection index
DI = tb.open_file(op.join(pdr_dir, 'detect/detect_index_hdr5.h5'), 'r')

detectid_obj = 5090068724  # example AGN

det_file_info = DI.root.DetectIndex.read_where('detectid == detectid_obj')[0]
survey   = det_file_info['survey'].decode()    # e.g. 'hdr5'
det_type = det_file_info['det_type'].decode()  # 'line' or 'cont'

# Choose correct H5 file
det_file_type = 'detect' if det_type == 'line' else 'cont'
det_file = tb.open_file(op.join(pdr_dir,
                                 f'detect/{det_file_type}_{survey}.h5'), 'r')

det_info = det_file.root.Detections.read_where('detectid == detectid_obj')[0]
coord   = SkyCoord(ra=det_info['ra'], dec=det_info['dec'], unit='deg')
shotid  = det_info['shotid']
ifuslot = det_info['ifuslot'].decode()
if det_type == 'line':
    cw = det_info['wave']  # central wavelength in Ang

# Get pipeline spectrum
spec_pipeline = det_file.root.Spectra.read_where('detectid == detectid_obj')[0]

# REQUIRED: Apply calibration correction
corr_file = np.loadtxt(op.join(pdr_dir, 'detect/wdcor.txt'))
spectrum  = spec_pipeline['spec1d'] / corr_file[:, 1]
spectrum /= 2.0  # convert from per-bin to per-Ang flux density

# ALWAYS close H5 files when done
det_file.close()
DI.close()
```

Detection index columns: detectid, shotid, ra, dec, wave, sn, healpix,
det_type ('line'/'cont'), survey, fiber_id. Queryable by HEALPix (Nside=215).

---

## 14. Notebook Curriculum Map

Notebooks are in `notebooks/` (clone of https://github.com/HETDEX/dexcube).
Run sequentially. Each depends on environment and files from earlier notebooks.

| # | File                                   | Key inputs             | Key outputs             | Science goal                       |
|---|----------------------------------------|------------------------|-------------------------|------------------------------------|
| 01| 01-DataModel+IFU-Index.ipynb           | --                     | ifu_data Table          | Data model, download ifu-index     |
| 02| 02-DownloadingCubes.ipynb              | ifu-index              | Local FITS cube         | Download a single cube             |
| 03| 03-DataCubeFormat.ipynb                | Local FITS cube        | --                      | HDU structure, units, WCS          |
| 04| 04-MaskingOptions.ipynb                | Local FITS cube        | Masked arrays           | Bitmask quality filtering          |
| 05| 05-CubeWidget.ipynb                    | Local FITS cube        | --                      | Interactive xyλ browser           |
| 06| 06-CoordinateQuery.ipynb               | ifu-index, RA/Dec      | Cube paths              | Find cubes by sky coordinate       |
| 07| 07-CollapsingCubes.ipynb               | Local FITS cube        | 2D images               | Narrow-band / continuum maps       |
| 08| 08-ExtractingSpectra.ipynb             | Local FITS cube        | 1D spectrum             | Circular aperture extraction       |
| 09| 09-CatalogExtractions.ipynb            | Catalog, cubes         | Astropy Table + spectra | Batch parallel extraction          |
| 10| 10-HETDEX-Source-Catalog.ipynb         | HPSC2 catalog          | --                      | Catalog structure, cross-matching  |
| 11| 11-Source-Look-Up.ipynb                | HPSC2, cubes, H5 files | --                      | Source lookup, ELiXer, detection DB|
| 12| 12-BatchDownloads-ForRemoteUsers.ipynb | ifu-index, catalog     | urls.txt, cubes         | Bulk download for remote users     |

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
| Access raw pipeline detections                           | 11 (H5 section)      |

---

## 15. Standard Example Objects Used in Notebooks

| Object | RA (deg) | Dec (deg) | z | Type | Used in |
|--------|----------|-----------|---|------|---------|
| Lyman Alpha Blob | 228.78581 | 51.268036 | 2.53 | LAB | Nb06, 07 |
| Changing-look AGN | 150.23189 | 2.363963 | -- | AGN (COSMOS) | Nb08, 12 |
| OII galaxy | 215.68578 | 52.11736 | 0.067 | galaxy | Nb07 RGB |
| Test cube | shotid=20190405020, ifuslot='034' | -- | -- | Used in Nb03-05 |

---

## 16. Access & Data Products

### JupyterHub (recommended — data pre-mounted)

1. Create TACC account: https://accounts.tacc.utexas.edu/register
2. Request HETDEX access: https://tacc.utexas.edu/portal/login?next=/tacc-user-portal/hetdex-access-request/
3. Sign in: https://jupyter.tacc.cloud
4. Clone notebooks: `git clone https://github.com/HETDEX/dexcube.git`

No persistent storage on the public JupyterHub. Download outputs before session ends.

### Docker (self-contained)

```bash
# Linux / Intel Mac
docker run --pull always --rm -p 8888:8888 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''

# Apple Silicon Mac (M1/M2/M3/M4) — add --platform flag
docker run --pull always --rm -p 8888:8888 \
  --platform linux/amd64 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''

# With Anthropic API key for LLM-assisted analysis
docker run --pull always --rm -p 8888:8888 \
  --platform linux/amd64 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''
```

### Available Data Files at PDR1 Base URL

| File | Size | Description |
|------|------|-------------|
| ifu-index.fits / .h5 / .txt | <200 MB | Master IFU manifest |
| hetdex_sc2_vX.X.fits / .dat | 11 GB | HPSC2 main source catalog |
| hetdex_sc2_spec_vX.X.fits | 11 GB | HPSC2 1D spectra for all sources |
| hetdex_sc2_detinfo_vX.X.fits | 11 GB | Supplemental detection info table |
| datacubes/SHOTID/*.fits | 7.4 TB | 431,713 IFU datacubes (~19 MB each) |
| detect/detect_hdrX.h5 | 1.7 TB | Raw emission line detection databases |
| detect/cont_hdrX.h5 | -- | Raw continuum detection databases |
| detect/detect_index_hdr5.h5 | -- | Master index for all detections |
| detect/wdcor.txt | -- | Calibration correction for raw H5 spectra |
| detect/elixer/NNNNN/*.jpg | 587 GB | ELiXer diagnostic reports (~150 KB each) |

---

## 17. Data Caveats and Limitations

### Early Data (2017)
Shotids beginning with `2017` correspond to early survey data with fewer IFUs
and poorer detector quality. Avoid for LAE science without manual inspection.

### Local Sky Subtraction
PDR1 uses local sky subtraction optimised for faint emission-line detection.
Not suitable for:
- Absolute surface-brightness measurements or intensity mapping
- Studies of very extended nearby galaxies (IFU-scale emission over-subtracted)

### Flux Sensitivity
~50% completeness at 1.1 x 10^-16 erg/s/cm^2. Not suited for luminosity
function measurements without completeness corrections.

### Source Detection on Datacubes
Source detection was done on internal fiber data. Independent detection on
PDR1 cubes recovers median S/N = 0.75 +/- 0.23 relative to catalog values.
Use BADDET bitmask (8192) when doing independent emission-line searches.

### Stacking
Raw cubes have ~1% sky residual per spectrum. Published stacking analyses
subtract a correction spectrum from ~200 random sky apertures per field.
This correction is NOT included in the datacubes.

### Spectral Extraction: Cube vs Pipeline
Cube aperture extractions agree with internal pipeline to ~5-10% (blue end
shows largest difference). Standard aperture in notebooks: r = 3.5 arcsec.
Note: spec in hdu['SPEC'] is already in erg/s/cm^2/Ang (divided by 2).
The raw H5 spec1d is per 2-Ang bin — always divide by 2 and apply wdcor.txt.

---

## 18. Common Errors and Gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| FileNotFoundError on ifu-index.fits | Not downloaded on Docker/local | Run startup bootstrap — it downloads automatically |
| ifu_data / ifu_coords not defined | Bootstrap not run | Always run Section 2 bootstrap before any query code |
| Flux factor of 2 too large | Treating per-bin as per-Ang | Divide DATA by 2.0 for flux density |
| Flux factor ~1e17 too large | Units not applied | DATA is in 1e-17 units; multiply by 1e-17 for CGS |
| WCS gives wrong coords | Using naxis=3 for spatial | Use `WCS(header).celestial` |
| Cube orientation wrong | Cubes aligned to HET PA | Always use WCS, never assume north-up |
| NaN in cube | Outside valid fiber region | Expected at cube spatial edges |
| get_spectra returns None | Coord not in cube footprint | Check `wcs.celestial.footprint_contains(coord)` first |
| flag=1 in ifu-index = good | Opposite of MASK HDU convention | ifu-index: flag=1=good; MASK HDU: 0=good |
| 2017 data noisy/artifacts | Early survey, few IFUs | Avoid 2017 shotids for LAE science |
| source_id duplicated | Multiple observations of same source | Same source_name, different source_id per observation |
| H5 file won't close | Forgot to call close() | Always call det_file.close() and DI.close() |
| Raw H5 spectrum too bright | Missing calibration correction | Apply wdcor.txt correction AND divide by 2 |
| Stack has residual sky bumps | Sky residual not in cubes | Subtract correction from ~200 random sky apertures |
| Catalog SPEC units differ | Already per-Ang unlike DATA | hdu['SPEC'] is erg/s/cm^2/Ang; DATA is per 2 Ang bin |

---

## 19. Software Environment

- Python 3.10+; see `requirements.txt` for pinned packages
- Key packages: astropy, numpy, matplotlib, ipywidgets, scipy, photutils, tables, joblib
- Use `%matplotlib widget` (not inline) for CubeWidget and interactive plots
- `from dexcube.cube_widget import CubeWidget` — requires JupyterLab + ipywidgets
- `from dexcube.get_spec import get_spectra` — main extraction utility

### Using Claude/LLM API Directly in Notebooks

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user",
               "content": "What is the HETDEX survey and how do I extract a spectrum?"}]
)
print(response.content[0].text)
```

---

## 20. Key References

- **PDR1 paper**: Mentuch Cooper et al. 2026 (submitted)
- **HPSC2 Zenodo**: https://doi.org/10.5281/zenodo.19581262
- **HETDEX Survey**: Gebhardt et al. 2021, ApJ 923, 217 — doi:10.3847/1538-4357/ac2e03
- **VIRUS instrument**: Hill et al. 2021, AJ 162, 298 — doi:10.3847/1538-3881/ac2c02
- **HPSC1**: Mentuch Cooper et al. 2023, ApJ 943, 177 — doi:10.3847/1538-4357/aca962
- **AGN Catalog 1**: Liu et al. 2022, ApJS 261, 24 — doi:10.3847/1538-4365/ac6ba6
- **AGN Catalog 2**: Liu et al. 2025, ApJS 276, 72 — doi:10.3847/1538-4365/ada4a5
- **ELiXer**: Davis et al. 2023a, ApJ 946, 86 — doi:10.3847/1538-4357/acb0ca
- **HETDEX-DESI VAC**: Landriau et al. 2025, ApJ 995, 220 — doi:10.3847/1538-4357/ae1ae6
- **LAE Profiles**: Mentuch Cooper et al. 2026, ApJ 1000, 38 — doi:10.3847/1538-4357/ae44f3
- **Dark Energy Explorers**: House et al. 2023, ApJ 950, 82 — doi:10.3847/1538-4357/accdd0
  https://www.zooniverse.org/projects/erinmc/dark-energy-explorers

### Citation Requirements

Papers using HETDEX PDR1 must cite the HET (Ramsey et al. 1998; Hill et al.
2021), VIRUS (Hill et al. 2021), and HETDEX survey (Gebhardt et al. 2021).
See https://hetdex.org/papers/ for full acknowledgement text.

---

## 21. Contact & Support

- **Data questions**: Erin Mentuch Cooper — erin.hetdex@gmail.com
- **GitHub issues**: https://github.com/HETDEX/dexcube/issues
- **HETDEX website**: https://hetdex.org
- **Data portal**: https://hetdex.org/data-results/
- **JupyterHub**: https://jupyter.tacc.cloud
