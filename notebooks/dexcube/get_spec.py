# get_spec.py
import os.path as op
import numpy as np

from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.coordinates import SkyCoord
import astropy.units as u

from photutils.aperture import CircularAperture


# ---- HETDEX mask bit definitions ----
MASK_BITS = {
    "MAIN":        0x00000001,
    "FTF":         0x00000002,
    "CHI2FIB":     0x00000004,
    "BADPIX":      0x00000008,
    "BADAMP":      0x00000010,
    "LARGEGAL":    0x00000020,
    "METEOR":      0x00000040,
    "BADSHOT":     0x00000080,
    "THROUGHPUT":  0x00000100,
    "BADFIB":      0x00000200,
    "SAT":         0x00000400,
    "BADCAL":      0x00000800,
    "PIXMASK":     0x00001000,
}


def _bits_from_names(names):
    """
    Convert bit names (str or list of str) or an int bitmask to an integer mask.
    Special string: "ALL_NONZERO" means any nonzero mask value.
    """
    if names is None:
        return 0
    if isinstance(names, int):
        return int(names)
    if isinstance(names, str):
        if names.upper() == "ALL_NONZERO":
            # handled specially by the caller
            return "ALL_NONZERO"
        names = [names]
    val = 0
    for n in names:
        key = str(n).upper()
        if key not in MASK_BITS:
            raise ValueError(f"Unknown mask bit name: {n}")
        val |= MASK_BITS[key]
    return val


def get_spectra(
    coord: SkyCoord,
    shotid,
    ifuslot,
    data_dir,
    radius: float = 3.5,        # arcsec
    padding_pix: int = 2,
    # ----- Masking controls -----
    # By default, keep only voxels with MASK == 0 (i.e., exclude ALL nonzero bits)
    exclude_bits="ALL_NONZERO",  # int bitmask or names or "ALL_NONZERO"
    keep_bits=None,              # bits to re-allow even if excluded
    include_only_bits=None,      # if set, keep only voxels that have ANY of these bits set
    # ----- Coverage handling -----
    min_coverage: float = 0.20,  # wavelengths with apcor < this become NaN
    # ----- Returns -----
    return_wave: bool = False,
):
    """
    Extract a 1D spectrum from a HETDEX IFU cube using a circular aperture with
    subpixel (fractional) pixel weighting and per-λ geometric coverage correction.

    Output units: 1e-17 erg s^-1 cm^-2 Å^-1 (per-Å), derived by dividing by SPECBW.
    Input cubes are assumed to be integrated per voxel per spectral bin.
    """
    # ---- resolve file path ----
    if isinstance(ifuslot, (int, np.integer)):
        ifus = f"{int(ifuslot):03d}"
    else:
        s = str(ifuslot)
        ifus = s if len(s) == 3 else s.zfill(3)

    cube_path = op.join(data_dir, "datacubes", str(shotid), f"dex_cube_{shotid}_{ifus}.fits")
    if not op.exists(cube_path):
        raise FileNotFoundError(f"Datacube not found: {cube_path}")

    # ---- open and read a tight subcube ----
    with fits.open(cube_path, memmap=True) as hdul:
        hdr  = hdul["DATA"].header
        wcs  = WCS(hdr)
        nlam, ny, nx = hdul["DATA"].shape

        # sky → pixel (celestial)
        x_pix, y_pix = wcs.celestial.world_to_pixel(coord)

        # pixel scale (deg/pix → arcsec/pix) – assume square for aperture radius
        sx_deg = proj_plane_pixel_scales(wcs.celestial)[0]
        sx_arcsec = float((sx_deg * u.deg).to(u.arcsec).value)
        r_pix = radius / sx_arcsec

        # -------- early reject: aperture completely off the IFU --------
        if (x_pix + r_pix) < 0 or (x_pix - r_pix) > (nx - 1) or \
           (y_pix + r_pix) < 0 or (y_pix - r_pix) > (ny - 1):
            return None

        # local bounds with padding (use end-exclusive +1 to avoid off-by-one empties)
        x_min = int(np.floor(x_pix - r_pix)) - padding_pix
        x_max = int(np.ceil (x_pix + r_pix)) + padding_pix + 1
        y_min = int(np.floor(y_pix - r_pix)) - padding_pix
        y_max = int(np.ceil (y_pix + r_pix)) + padding_pix + 1

        # clip to IFU
        x_min = max(0, x_min); x_max = min(nx, x_max)
        y_min = max(0, y_min); y_max = min(ny, y_max)

        # if nothing remains after clipping, just return None quietly
        if (x_min >= x_max) or (y_min >= y_max):
            return None

        # read subcube planes only
        flux_cube  = hdul["DATA"].section [:, y_min:y_max, x_min:x_max].astype(np.float32, copy=False)
        error_cube = hdul["ERROR"].section[:, y_min:y_max, x_min:x_max].astype(np.float32, copy=False)
        mask_cube  = hdul["MASK"].section [:, y_min:y_max, x_min:x_max]
        data_hdr   = hdr.copy()

    nlam, ny_sub, nx_sub = flux_cube.shape

    # ---- wavelength array (Å) & spectral bin width (Å) ----
    spec_bw = float(data_hdr.get("SPECBW", 2.0))
    try:
        wave = WCS(data_hdr).sub(['spectral']).pixel_to_world(np.arange(nlam)).to_value(u.AA).astype(np.float32)
    except Exception:
        # fallback linear solution
        crval3 = float(data_hdr.get("CRVAL3", 3470.0))
        cdelt3 = float(data_hdr.get("CDELT3", 2.0))
        crpix3 = float(data_hdr.get("CRPIX3", 1.0))
        wave = (crval3 + (np.arange(nlam, dtype=np.float32) + 1 - crpix3) * cdelt3).astype(np.float32)

    # ---- center in subimage coords ----
    x0 = float(x_pix - x_min)
    y0 = float(y_pix - y_min)

    # ---- masking logic ----
    inc = _bits_from_names(include_only_bits)
    exc = _bits_from_names(exclude_bits)
    kep = _bits_from_names(keep_bits)

    if inc not in (None, 0):
        # Keep only voxels with any of these bits set
        if inc == "ALL_NONZERO":
            good_vox = (mask_cube != 0)
        else:
            inc_mask = int(inc)
            good_vox = (mask_cube & inc_mask) != 0
    else:
        # Default path: exclude bits; allow keep_bits back in
        if exc == "ALL_NONZERO":
            base_good = (mask_cube == 0)
        else:
            exc_mask = int(exc) if exc is not None else 0
            base_good = (mask_cube & exc_mask) == 0

        if kep in (None, 0):
            good_vox = base_good
        else:
            if kep == "ALL_NONZERO":
                # allow any nonzero bits back in (i.e., effectively disable exclude)
                good_vox = np.ones_like(base_good, dtype=bool)
            else:
                keep_mask = int(kep)
                good_vox = base_good | ((mask_cube & keep_mask) != 0)

    # apply mask: anything not good → NaN
    flux_use = np.where(good_vox, flux_cube, np.nan)
    var_use  = np.where(good_vox, error_cube**2, np.nan)

    # ---- fractional aperture weights (subpixel exact) ----
    ap = CircularAperture((x0, y0), r=r_pix)
    weights = ap.to_mask(method="exact").to_image((ny_sub, nx_sub)).astype(np.float32)  # [0,1]
    total_w = float(np.sum(weights))
    if total_w <= 0:
        nan = np.full(nlam, np.nan, dtype=np.float32)
        return (nan, nan, nan, wave) if return_wave else (nan, nan, nan)

    # ---- per-λ coverage fraction (geometry × data availability) ----
    #
    # A voxel is considered missing if any of the following are true:
    #   (a) it was excluded by the bitmask logic above (flux_use is NaN)
    #   (b) ERROR == 0  → no fiber coverage at this spatial/spectral position
    #   (c) |flux| < 1e-8 → unfilled edge pixels not caught by the mask
    #
    # apcor[λ] = sum(weights * has_data[λ]) / total_w
    has_data = (
        np.isfinite(flux_use) &         # passes bitmask
        (error_cube != 0) &             # has fiber coverage
        (np.abs(flux_cube) >= 1e-8)     # not an unfilled edge pixel
    ).astype(np.float32)                # shape (nlam, ny_sub, nx_sub)

    apcor = (np.sum(weights[np.newaxis, :, :] * has_data, axis=(1, 2)) / total_w).astype(np.float32)

    # ---- weighted sums ----
    f_sum = np.nansum(flux_use * weights, axis=(1, 2)).astype(np.float32)
    v_sum = np.nansum(var_use  * (weights**2), axis=(1, 2)).astype(np.float32)
    e_sum = np.sqrt(v_sum, dtype=np.float32)

    # ---- correct for partial coverage & per-Å ----
    with np.errstate(invalid="ignore", divide="ignore"):
        spectrum = (f_sum / apcor) / spec_bw
        error    = (e_sum / apcor) / spec_bw

    spectrum = spectrum.astype(np.float32)
    error    = error.astype(np.float32)

    # guard: low coverage → NaN
    bad_cov = (~np.isfinite(apcor)) | (apcor <= 0) | (apcor < float(min_coverage))
    spectrum[bad_cov] = np.nan
    error[bad_cov]    = np.nan
    apcor[bad_cov]    = np.nan

    if return_wave:
        return spectrum, error, apcor, wave
    return spectrum, error, apcor
