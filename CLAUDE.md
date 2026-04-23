# CLAUDE.md
# Auto-loaded by Claude Code, Cursor, and other LLM coding assistants.
# Full survey context is in HETDEX_CONTEXT.md in this repo root.
# Reference: Mentuch Cooper et al. 2026 (PDR1 paper)

## What This Repo Is

`dexcube` is a set of 12 sequential Jupyter notebooks for accessing and analysing
HETDEX Public Data Release 1 (PDR1) — 431,713 IFU datacubes covering 86.67 deg^2
of optical spectroscopy (3470-5540 Ang, R~800) from the Hobby-Eberly Telescope.

Run notebooks in order (01 through 12). Each builds on the previous.

---

## 0. STARTUP BOOTSTRAP — Run This First in Every Session

**Before writing any analysis code, always run this complete bootstrap block.**
It sets `pdr_dir`, creates the directory if needed, and downloads `ifu-index.fits`
if it is missing. On the HETDEX JupyterHub the data is pre-mounted and nothing
is downloaded. On Docker or any remote/local environment the index file is
fetched automatically from the public URL.

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

---

## 1. Data Paths Reference

Environment-specific paths for `pdr_dir`:
- **HETDEX JupyterHub** (https://jupyter.tacc.cloud): `/home/jovyan/Hobby-Eberly-Public/HETDEX/pdr/pdr1/`
- **TACC Stockyard**: `/corral-repl/utexas/Hobby-Eberly-Telesco/public/HETDEX/pdr/pdr1/`
- **Docker container**: `/home/jovyan/work/pdr1/`

---

## 2. Datacube File Path Convention

```python
datacube_path = op.join(pdr_dir, 'datacubes', str(shotid),
                        'dex_cube_{}_{}.fits'.format(shotid, ifuslot))
# Example: pdr1/datacubes/20190405020/dex_cube_20190405020_034.fits
```

---

## 3. Downloading Datacubes (Notebook 02)

The ifu-index.fits is handled by the bootstrap above. For datacubes themselves:

### Download a single cube
```python
import os, subprocess
from urllib.parse import urlsplit

base_url = "http://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/datacubes"
shotid = 20190405020
ifuslot = '034'

filename = f"dex_cube_{shotid}_{ifuslot}.fits"
url = f"{base_url}/{shotid}/{filename}"

base_url_path = '/hetdex/HETDEX/pdr/pdr1/'
path = urlsplit(url).path
rel_path = path.split(base_url_path, 1)[-1]
local_path = os.path.join(pdr_dir, rel_path)

os.makedirs(os.path.dirname(local_path), exist_ok=True)
if not op.exists(local_path):
    subprocess.run(['wget', '-q', '-O', local_path, url])
    print(f"Downloaded: {rel_path}")
else:
    print(f"Already exists: {local_path}")
```

### Batch download via wget (terminal)
```bash
# Single threaded
wget --cut-dirs=4 -nH -x -i urls.txt

# Parallel (4 workers — don't use too many or server will throttle)
cat urls.txt | xargs -n 1 -P 4 wget --cut-dirs=4 -nH -x
```

---

## 4. Datacube Format — CRITICAL FACTS

### HDU structure
```python
from astropy.io import fits
from astropy.wcs import WCS

hdul = fits.open(datacube_path)
flux   = hdul["DATA"].data   # shape (1036, 104, 104) — (wave, y, x)
error  = hdul["ERROR"].data  # same shape and units as DATA
mask   = hdul["MASK"].data   # same shape, integer bitmask
header = hdul["DATA"].header
wcs    = WCS(header)
hdul.close()
```

### Units — DO NOT GET WRONG
- **DATA**: 10^-17 erg s^-1 cm^-2 **per 2 Ang bin** (NOT per Ang)
  - Divide by 2.0 to get flux density in erg/s/cm^2/Ang
  - Multiply by 1e-17 to get CGS
- Spaxels outside valid fiber region = **NaN**

### Dimensions — always fixed
- Shape: **(1036, 104, 104)** — wavelength x y x
- Wavelength: 3470-5540 Ang in 2 Ang steps
- Spatial: 104 x 104 spaxels at 0.5 arcsec/spaxel = 52" x 52"

### Wavelength array
```python
import numpy as np
wave = np.linspace(3470, 5540, num=1036)
# OR from WCS:
wcs_spectral = WCS(header).sub(['spectral'])
wavelengths = wcs_spectral.pixel_to_world(np.arange(flux.shape[0]))
```

### WCS — always use celestial for spatial
```python
wcs_celestial = WCS(header).celestial  # spatial-only WCS

# Convert sky coord to pixel
from astropy.coordinates import SkyCoord
import astropy.units as u
coord = SkyCoord(ra=228.78581*u.deg, dec=51.268036*u.deg)
x_pix, y_pix = wcs_celestial.world_to_pixel(coord)

# Check exact coverage
inside = wcs_celestial.footprint_contains(coord)

# Get pixel scale
from astropy.wcs import WCS
pixel_scale = np.abs(wcs.proj_plane_pixel_scales()[0]).to(u.arcsec).value
```

**Cubes are NOT north-up.** Always use WCS. ADR is already corrected.

---

## 5. Masking (Notebook 04)

**Bitmask convention: 0 = GOOD. Non-zero = flagged.**
This is OPPOSITE of `flag` in ifu-index.fits where 1=good, 0=bad.

### Full bitmask table
| Integer | Name       | Description                              | Always use? |
|---------|------------|------------------------------------------|-------------|
| 0       | Good       | No flag                                  | --          |
| 1       | MAIN       | Flagged in reduction (calfibe==0.0)      | YES         |
| 2       | FTF        | Fiber-to-fiber deviation > 0.5           | YES         |
| 4       | CHI2FIB    | chi2fib > 150                            | YES         |
| 8       | BADPIX     | Bad pixel region                         | YES         |
| 16      | BADAMP     | Bad amplifier                            | YES         |
| 32      | LARGEGAL   | Within large galaxy mask                 | optional    |
| 64      | METEOR     | Known meteor track                       | YES         |
| 128     | BADSHOT    | Bad shot (not in PDR1)                   | N/A         |
| 256     | THROUGHPUT | Throughput < 0.08 (not in PDR1)          | N/A         |
| 512     | BADFIB     | Known bad fiber                          | YES         |
| 1024    | SAT        | Satellite track                          | recommended |
| 2048    | BADCAL     | Sky/calibration issue at wavelength      | optional    |
| 4096    | PIXMASK    | Native spectrum == 0                     | YES         |
| 8192    | BADDET     | ML-flagged detection location            | for searches|

### Standard masking patterns
```python
# Minimum mask (always use this)
good = (mask & (1 | 2 | 4 | 8 | 16)) == 0

# Full mask for emission line searches
good = mask == 0

# Apply mask to flux cube
flux[np.where(mask > 0)] = np.nan

# Apply mask but keep BADCAL (e.g. to recover line at 3640 Ang)
good_mask_values = (mask == 0) | (mask == 2048)
data_mask = (~good_mask_values) | (flux == 0)
flux[data_mask] = np.nan

# Find IFUs with meteors from ifu-index
met_indices = np.where(ifu_data['flag_meteor'] < 0.5)[0]

# Isolate only meteor-flagged pixels
meteor_mask = (mask_slice & 64) != 0
```

---

## 6. Loading the IFU Index (Notebook 01)

```python
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

ifu_data = Table.read(op.join(pdr_dir, 'ifu-index.fits'))

# Key columns:
# shotid       int64   observation ID (YYYYMMDDNNN)
# ifuslot      str     IFU slot identifier e.g. '034'
# ra_cen       float32 IFU center RA (deg)
# dec_cen      float32 IFU center Dec (deg)
# flag         float32 1=fully useable, 0=fully flagged (NOTE: 1=good!)
# flag_badamp  float32 fraction unaffected by bad amp
# flag_meteor  float32 fraction unaffected by meteor
# fwhm_virus   float32 seeing FWHM (arcsec)
# response_4540 float32 system throughput at 4540 Ang

# Build SkyCoord array of all IFU centers
ifu_coords = SkyCoord(ra=ifu_data['ra_cen']*u.deg,
                      dec=ifu_data['dec_cen']*u.deg)
```

---

## 7. Coordinate Queries (Notebook 06)

### Single coordinate search
```python
coord = SkyCoord(ra=228.78581*u.deg, dec=51.268036*u.deg)

# Find IFUs within 37 arcsec (IFU radius ~26 arcsec)
sel = coord.separation(ifu_coords) < 37*u.arcsec

# Get cube paths
for row in ifu_data[sel]:
    shotid  = row['shotid']
    ifuslot = row['ifuslot']
    datacube_path = op.join(pdr_dir, 'datacubes', str(shotid),
                            'dex_cube_{}_{}.fits'.format(shotid, ifuslot))
    print(datacube_path)

# Check exact WCS coverage
with fits.open(datacube_path, memmap=False) as hdul:
    w = WCS(hdul['DATA'].header).celestial
    inside = w.footprint_contains(coord)
```

### Catalog cross-match (many coordinates)
```python
from astropy.table import hstack, unique

catalog_coords = SkyCoord(ra=catalog['ra'], dec=catalog['dec'], unit='deg')

# All IFUs overlapping any catalog source
idx_ifu, idx_catalog, d2d, d3d = catalog_coords.search_around_sky(
    ifu_coords, 37*u.arcsec)

# Build matched table
table = hstack([catalog_coords[idx_catalog], catalog[idx_catalog],
                ifu_data[idx_ifu]])
table.rename_column('col0', 'coords')

# Get unique IFU list
ifulist = unique(table['shotid', 'ifuslot'])
ifu_pairs = [(int(row['shotid']), str(row['ifuslot'])) for row in ifulist]
```

---

## 8. Collapsing Cubes (Notebook 07)

### Narrowband image at known wavelength
```python
wave = np.linspace(3470, 5540, num=1036)
wave_src = 4295.9  # Ang — e.g. Lya at z=2.53

# Apply mask
flux[np.where(mask > 0)] = np.nan

# Narrow-band collapse (+/- 10 Ang)
z_index = np.abs(wave_src - wave) < 10
flux_nb = np.nansum(flux[z_index, :, :], axis=0)
error_nb = np.sqrt(np.nansum(error[z_index, :, :]**2, axis=0))

# Broadband continuum collapse (3800-5200 Ang)
z_index_cont = (wave >= 3800) & (wave <= 5200)
flux_cont = np.nansum(flux[z_index_cont, :, :], axis=0)

# Convert center coord to pixel for plotting
x_center, y_center = wcs.celestial.world_to_pixel(coord)
```

### Continuum-subtracted emission line map
```python
redshift = 0.067
waveoii = 3727.8
dwave = 10  # half-width in Ang

z_index = np.abs(waveoii*(1. + redshift) - wave) < dwave
flux_oii = np.nansum(flux[z_index, :, :], axis=0)

# Subtract continuum contribution
dw_nb = 2*dwave
dw_cont = wave_hi - wave_lo
flux_cont_sub = dw_nb * (flux_cont / dw_cont)
line_map = flux_oii - flux_cont_sub
```

---

## 9. Spectral Extraction (Notebook 08)

### Simple circular aperture extraction
```python
import numpy as np
from astropy.wcs import WCS
import astropy.units as u

r_arcsec = 2.0  # aperture radius

# Get pixel coords of source
x_pix, y_pix = wcs.celestial.world_to_pixel(coord)
x_pix, y_pix = float(x_pix), float(y_pix)

# Pixel scale
pixel_scale = np.abs(wcs.proj_plane_pixel_scales()[0]).to(u.arcsec).value
r_pix = r_arcsec / pixel_scale

# Boolean aperture mask
ny, nx = flux.shape[1:]
yy, xx = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
circular_aperture_mask = (xx - x_pix)**2 + (yy - y_pix)**2 <= r_pix**2

# Extract spectrum
spectrum = np.nansum(flux[:, circular_aperture_mask], axis=1)
spectrum[spectrum == 0] = np.nan

# Get wavelength array from WCS
wcs_spectral = WCS(header).sub(['spectral'])
wavelengths = wcs_spectral.pixel_to_world(np.arange(flux.shape[0])).to(u.Angstrom)
```

### Aperture-corrected extraction with photutils (recommended for science)
```python
from photutils.aperture import CircularAperture

r_arcsec = 3.5  # standard aperture in notebooks

ap = CircularAperture((x_pix, y_pix), r=r_pix)
apmask = ap.to_mask(method='exact')
if isinstance(apmask, list):
    apmask = apmask[0]

W = apmask.to_image((ny, nx))   # fractional weights [0-1]
A_tot = W.sum()                  # total aperture area in pixels

# Per wavelength slice: weighted sum + aperture correction
spectrum = np.zeros(flux.shape[0])
for i in range(flux.shape[0]):
    slice_flux = flux[i]
    valid = np.isfinite(slice_flux)
    A_valid = (W * valid).sum()
    if A_valid > 0:
        spectrum[i] = np.nansum(slice_flux * W) * (A_tot / A_valid)
    else:
        spectrum[i] = np.nan
```

### Use the built-in get_spectra function (Notebooks 09 and 11)
```python
from dexcube.get_spec import get_spectra

# Basic usage
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

# Exclude all nonzero bits but allow BADCAL through
spec, err, ap = get_spectra(coord, shotid, ifuslot, data_dir=pdr_dir,
                             exclude_bits="ALL_NONZERO",
                             keep_bits="BADCAL")

# No masking at all
spec, err, ap, wave = get_spectra(
    coord, shotid, ifuslot, pdr_dir,
    radius=3.5,
    exclude_bits=None,
    include_only_bits=None,
    return_wave=True
)
```

---

## 10. Batch Catalog Extractions (Notebook 09)

```python
from dexcube.get_spec import get_spectra
from multiprocessing import Pool
from tqdm import tqdm
import time

# Define wrapper for parallel processing
def process_row(row):
    return get_spectra(row['coords'], row['shotid'], row['ifuslot'],
                       data_dir=pdr_dir)

# Run in parallel (20 workers typical for JupyterHub)
t0 = time.time()
with Pool(processes=20) as pool:
    results = pool.map(process_row, table)
t1 = time.time()
print('Done in {:3.2f} min.'.format((t1-t0)/60))

# Store results in astropy Table
from astropy.table import Column
import numpy as np

num_rows = len(table)
nan_array = np.full(1036, np.nan, dtype=np.float32)
table.add_column(Column(data=np.tile(nan_array, (num_rows, 1)), name='spectrum'))
table.add_column(Column(data=np.tile(nan_array, (num_rows, 1)), name='error'))
table.add_column(Column(data=np.tile(nan_array, (num_rows, 1)), name='apcor'))

for i, row in enumerate(table):
    if results[i] is not None:
        spectrum, error, apcor = results[i]
        table['spectrum'][i] = spectrum
        table['error'][i] = error
        table['apcor'][i] = apcor

table.write('output_spectra.fits', overwrite=True)
```

---

## 11. HPSC2 Source Catalog (Notebook 10)

```python
from astropy.io import fits
from astropy.table import Table
import numpy as np

# Path to catalog
path_to_cat = op.join(pdr_dir, 'hetdex_source_catalog_2/')
version = 'v1.5'  # check for latest version in directory

# --- Main catalog (no spectra) ---
source_table = Table.read(op.join(path_to_cat,
                                   'hetdex_sc2_{}.fits'.format(version)))

# --- Catalog with spectra ---
hdu = fits.open(op.join(path_to_cat,
                         'hetdex_sc2_spec_{}.fits'.format(version)))
spec     = hdu['SPEC'].data        # shape (1036, N_sources) — units: 1e-17 erg/s/cm^2/Ang
spec_err = hdu['SPEC_ERR'].data    # same shape
wave_rect = hdu['WAVELENGTH'].data # shape (1036,) in Angstrom

# --- Detection Info Table ---
det_table = Table.read(op.join(path_to_cat,
                                'hetdex_sc2_detinfo_{}.fits'.format(version)))
det_table.convert_bytestring_to_unicode()
```

### Key catalog columns
```python
# source_table key columns:
# source_name   str     HETDEX IAU name e.g. 'HETDEX J123449.19+511733.7'
# source_id     int     unique per observation (same source = same name, different id)
# shotid        int     observation ID (YYYYMMDDNNN)
# ifuslot       str     IFU slot
# RA, DEC       float   source coordinates (ICRS deg)
# z_hetdex      float   spectroscopic redshift
# source_type   str     'lae', 'oii', 'agn', 'lzg', 'star'
# flux_lya      float   Lya flux (1e-17 erg/s/cm^2), extinction-corrected
# flux_oii      float   [OII] flux (same units)
# p_conf        float   RF classifier confidence (1=high, 0=low)
# p_cnn         float   CNN classifier confidence (1=high, 0=low)
# sn            float   S/N; -999 for continuum sources
# gmag          float   HETDEX g magnitude
# flag_aper     int     1=use flux_aper; 0=use PSF flux; -1=no OII
# Bad values: -999.0 for floats, 'n/a' for strings
```

### Common catalog queries
```python
# Select by source type
sel_lae = source_table['source_type'] == 'lae'
sel_oii = source_table['source_type'] == 'oii'

# Quality cuts for robust LAE sample
sel_good = (source_table['p_conf'] >= 0.5) & (source_table['p_cnn'] >= 0.5)

# Select by date (shotid encodes date)
sel_date = source_table['shotid'] > 20240600000

# Select bright LAEs
sel_flux = source_table['flux_lya'] > 15

# Combined
sel = sel_lae & sel_good & sel_flux

# Get spectra for selection
selected_spectra = spec[:, sel]     # shape (1036, N_selected)
selected_wave = wave_rect            # shared wavelength array

# Coordinate search
from astropy.coordinates import SkyCoord
import astropy.units as u
source_coords = SkyCoord(ra=source_table['RA'], dec=source_table['DEC'])
coord = SkyCoord(ra=220.21432*u.deg, dec=52.095898*u.deg)
sel_match = np.where(source_coords.separation(coord) < 1.*u.arcsec)[0]

# Plot spectrum for matched source
redshift = source_table['z_hetdex'][sel_match][0]
lya_wave = 1216 * (redshift + 1)
plt.plot(wave_rect, spec[:, sel_match[0]])
plt.xlim(lya_wave - 50, lya_wave + 50)
```

---

## 12. Source Lookup and ELiXer Reports (Notebook 11)

```python
# Load a source from catalog and open its cube
shotid   = row['shotid']
ifuslot  = row['ifuslot']
wave_src = row['wave']  # from det_table
coord    = SkyCoord(ra=row['ra']*u.deg, dec=row['dec']*u.deg)

datacube_path = op.join(pdr_dir, 'datacubes', str(shotid),
                         'dex_cube_{}_{}.fits'.format(shotid, ifuslot))

hdul = fits.open(datacube_path)
flux  = hdul["DATA"].data
error = hdul["ERROR"].data
mask  = hdul["MASK"].data
flux[np.where((mask > 0) | (flux == 0.0))] = np.nan
header = hdul["DATA"].header
wave   = np.linspace(3470, 5540, num=1036)
wcs    = WCS(header)

# Load a subcube around source (faster for large cubes)
size  = 10   # arcsec side
wsize = 40   # spectral slice in Ang
x_pix, y_pix = wcs.celestial.world_to_pixel(coord)
from astropy.wcs.utils import proj_plane_pixel_scales
pixel_scale_arcsec = proj_plane_pixel_scales(wcs.celestial)[0] * 3600  # deg->arcsec
r_pix = size / pixel_scale_arcsec / 2

nz, ny, nx = hdul['DATA'].shape
x_min = max(0, int(np.floor(x_pix - r_pix)))
x_max = min(nx, int(np.ceil(x_pix + r_pix)) + 1)
y_min = max(0, int(np.floor(y_pix - r_pix)))
y_max = min(ny, int(np.ceil(y_pix + r_pix)) + 1)
wslice = np.abs(wave - wave_src) < wsize/2

flux_cube  = hdul['DATA'].data[wslice, y_min:y_max, x_min:x_max].astype(float)
error_cube = hdul['ERROR'].data[wslice, y_min:y_max, x_min:x_max].astype(float)

# View ELiXer report for a detection
from IPython.display import Image, display
det = row['detectid']
prefix = str(det)[:5]
url = f"https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/detect/elixer/{prefix}/{det}.jpg"
display(Image(url=url, width=900))
```

---

## 13. Raw Detection Databases (Notebook 11)

```python
import tables as tb

# Open detection index
DI = tb.open_file(op.join(pdr_dir, 'detect/detect_index_hdr5.h5'), 'r')

detectid_obj = 5090068724  # example AGN

det_file_info = DI.root.DetectIndex.read_where('detectid == detectid_obj')[0]
survey   = det_file_info['survey'].decode()
det_type = det_file_info['det_type'].decode()

# Choose line or continuum file
det_file_type = 'detect' if det_type == 'line' else 'cont'
det_file = tb.open_file(op.join(pdr_dir,
                                 f'detect/{det_file_type}_{survey}.h5'), 'r')

det_info = det_file.root.Detections.read_where('detectid == detectid_obj')[0]
coord    = SkyCoord(ra=det_info['ra'], dec=det_info['dec'], unit='deg')
shotid   = det_info['shotid']
ifuslot  = det_info['ifuslot'].decode()
if det_type == 'line':
    cw = det_info['wave']  # central wavelength in Ang

# Get pipeline spectrum
spec_pipeline = det_file.root.Spectra.read_where('detectid == detectid_obj')[0]

# Fix calibration issue in raw H5 spectra
import numpy as np
corr_file = np.loadtxt(op.join(pdr_dir, 'detect/wdcor.txt'))
spectrum = spec_pipeline['spec1d'] / corr_file[:, 1]
spectrum /= 2.0  # convert to erg/s/cm^2/Ang (divide by 2 Ang bin width)

# Always close H5 files when done
det_file.close()
DI.close()
```

---

## 14. CubeWidget (Notebook 05)

```python
from dexcube.cube_widget import CubeWidget

# Requires %matplotlib widget (not inline)
hdul = fits.open(datacube_path)
w = CubeWidget(hdu=hdul)
# Click on spatial region to see spectrum at that pixel
# Use play button or slider to scan through wavelengths
```

---

## 15. Standard Example Targets Used in Notebooks

| Target | RA (deg) | Dec (deg) | Type | Notes |
|--------|----------|-----------|------|-------|
| Lyman Alpha Blob | 228.78581 | 51.268036 | LAB z=2.53 | Nb07 example |
| Changing-look AGN | 150.23189 | 2.363963 | AGN (COSMOS) | Nb08, 12 example |
| OII galaxy | 215.68578 | 52.11736 | z=0.067 galaxy | Nb07 RGB example |
| Test cube | shotid=20190405020, ifuslot='034' | -- | Used in Nb03-05 |

---

## 16. Common Mistakes to Avoid

1. **Missing ifu-index.fits**: Always run the Section 0 bootstrap first. Without it, `ifu_data` and `ifu_coords` don't exist and every query will fail. If `ifu-index.fits` is missing on Docker/local, the bootstrap downloads it automatically.
2. **Flux units**: DATA is per 2 Ang bin. Divide by 2 for flux density in erg/s/cm^2/Ang.
2. **Mask convention**: `mask == 0` is GOOD in MASK HDU; `flag == 1` is GOOD in ifu-index.
3. **Hardcoded paths**: always use pdr_dir variable, never absolute paths.
4. **North-up assumption**: cubes are rotated to HET PA. Always use WCS.
5. **ADR**: already corrected in public cubes. Do not correct again.
6. **2017 data**: lower quality. Avoid for LAE science.
7. **Local sky subtraction**: PDR1 not suited for intensity mapping or absolute SB.
8. **source_id**: same source observed N times = same source_name but N different source_id values.
9. **Close H5 files**: always call `det_file.close()` and `DI.close()` after use.
10. **Stacking residuals**: raw cubes have ~1% sky residual. Subtract correction spectrum for stacks.
11. **get_spectra returns None**: cube doesn't cover the coordinate. Check `inside` first.
12. **Catalog spectra units**: SPEC in hdu is erg/s/cm^2/Ang (already /2), unlike raw DATA.

---

## 17. Key External Links

- Data portal: https://hetdex.org/data-results/
- JupyterHub: https://jupyter.tacc.cloud
- PDR1 base URL: https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/
- HPSC2 Zenodo: https://doi.org/10.5281/zenodo.19581262
- Contact: erin.hetdex@gmail.com
