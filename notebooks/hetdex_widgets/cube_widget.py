from astropy import units as u
import numpy as np
from astropy.table import Table
from astropy.wcs import WCS
from astropy.nddata import NDData
from scipy.ndimage import gaussian_filter1d
from ginga.AstroImage import AstroImage
from astrowidgets import ImageWidget
import ipywidgets as widgets
from IPython.display import display
import plotly.graph_objects as go
from matplotlib import pyplot as plt
import matplotlib.colors
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

plt.ioff()
plt.rcParams.update({'font.size': 18})


def wavelength_to_rgb(wavelength, gamma=0.8):
    wavelength = float(wavelength)/10
    if 380 <= wavelength <= 750:
        A = 1.
    else:
        A = 0.5
    w = np.clip(wavelength, 380., 750.)
    if 380 <= w <= 440:
        attenuation = 0.3 + 0.7 * (w - 380) / (440 - 380)
        R = ((-(w - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif 440 < w <= 490:
        R = 0.0; G = ((w - 440) / (490 - 440)) ** gamma; B = 1.0
    elif 490 < w <= 510:
        R = 0.0; G = 1.0; B = (-(w - 510) / (510 - 490)) ** gamma
    elif 510 < w <= 580:
        R = ((w - 510) / (580 - 510)) ** gamma; G = 1.0; B = 0.0
    elif 580 < w <= 645:
        R = 1.0; G = (-(w - 645) / (645 - 580)) ** gamma; B = 0.0
    else:
        attenuation = 0.3 + 0.7 * (750 - w) / (750 - 645)
        R = (1.0 * attenuation) ** gamma; G = 0.0; B = 0.0
    return (R, G, B, A)


class CubeWidget(ImageWidget):
    def __init__(self,
                 hdu=None,
                 im=None,
                 wcs=None,
                 show_rainbow=True,
                 display_unit=None,   # e.g., u.AA, u.nm; if None, use Å
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ---- Load data & WCS ----
        if hdu is not None:
            try:
                self.im = hdu.data
                self.wcs = WCS(hdu.header)
            except AttributeError:
                self.im = hdu[1].data
                self.wcs = WCS(hdu[1].header)
        elif im is not None:
            self.im = im
            self.wcs = wcs
        else:
            raise ValueError("Provide a 3D HDU or (im, wcs)")

        if self.im.ndim != 3:
            raise ValueError("CubeWidget expects a 3D cube with shape (nwave, ny, nx)")

        self.nddata = NDData(self.im, wcs=self.wcs)
        self.load_nddata(self.nddata, n=0)

        # ---- Spectral axis bookkeeping (units-aware) ----
        self.nwave = int(self.im.shape[0])

        # Native spectral unit from WCS (fallback: Å)
        try:
            native_unit = self.wcs.wcs.cunit[2] or ''
            self.native_unit = u.Unit(native_unit) if native_unit != '' else u.AA
        except Exception:
            self.native_unit = u.AA

        self.dwave_native = self.wcs.wcs.cdelt[2] * self.native_unit
        self.wave0_native  = self.wcs.wcs.crval[2] * self.native_unit

        # Always use Ångström for display unless user overrides
        if display_unit is None:
            self.display_unit = u.AA
        else:
            self.display_unit = u.Unit(display_unit)

        # Precompute wavelength array for plotting (in display units)
        idx = np.arange(self.nwave)
        self.wavelengths = (self.wave0_native + idx * self.dwave_native).to(self.display_unit).value

        self.show_rainbow = show_rainbow
        self.single_plots = False
        self.cuts = 'stddev'

        # ---- Index-based controls (robust to any units) ----
        self.idx_widget = widgets.IntSlider(
            description='Slice',
            min=0,
            max=self.nwave - 1,
            step=1,
            value=min(self.nwave // 2, self.nwave - 1),
            continuous_update=False,
        )
        self.slider = widgets.interactive(self.show_slice, idx=self.idx_widget)

        self.smooth_slider = widgets.IntSlider(
            description='Smooth σ',
            min=0, max=10, step=1, value=0,
            continuous_update=False
        )

        self.animate_button = widgets.Button(
            description="Scan Cube",
            disabled=False,
            button_style="success",
            tooltip="Click to scan along wavelength"
        )

        self.single_plot_button = widgets.Checkbox(
            description='Display Single Spectrum',
            value=False,
            tooltip='Plot one line at a time',
        )

        # Plot for spectra
        self._cur_islice = 0
        self._cur_ix = None
        self._cur_iy = None
        self.line_plot = go.FigureWidget()
        self.line_plot.update_layout(template='none')

        # Big wavelength label above the line plot
        self.wave_title = widgets.HTML()

        if self.show_rainbow:
            self.set_rainbow()

        # Play widget scans indices (always int-safe)
        self.scan = widgets.Play(
            value=self.idx_widget.value,
            min=0,
            max=self.nwave - 1,
            step=1,
            description="Scan Cube",
            disabled=False,
        )
        widgets.jslink((self.scan, "value"), (self.idx_widget, "value"))

        # Layout
        left_panel = widgets.VBox([widgets.HBox([self.idx_widget, self.scan]), self])
        right_panel = widgets.VBox([self.wave_title, self.line_plot, self.smooth_slider, self.single_plot_button])
        self.all_box = widgets.HBox([left_panel, right_panel])
        display(self.all_box)

        # Initialize wavelength label once UI is shown
        self._update_wave_label()

        # Observers
        self.smooth_slider.observe(self.plot_spec, names='value')

    def load_nddata(self, nddata, n=0):
        self.image = AstroImage()
        self.image.load_nddata(nddata, naxispath=[n])
        self._viewer.set_image(self.image)

    def _mouse_click_cb(self, viewer, event, data_x, data_y):
        self._cur_ix = int(round(data_x))
        self._cur_iy = int(round(data_y))
        self.plot_spec()

        if self.single_plot_button.value:
            self.reset_markers()

        if self._cur_ix is not None and self._cur_iy is not None:
            mrk_tab = Table(names=["x", "y"])
            mrk_tab.add_row([self._cur_ix, self._cur_iy])
            self.marker = {"color": 'red', "radius": 1, "type": "circle"}
            self.add_markers(mrk_tab)

    def plot_spec(self, trace_freeze=False):
        if self._cur_ix is None or self._cur_iy is None:
            return
        if self.image is None:
            return

        mddata = self.image.get_mddata()

        try:
            spectrum = mddata[:, self._cur_iy, self._cur_ix]
        except IndexError:
            return

        if self.smooth_slider.value > 0:
            spectrum = gaussian_filter1d(spectrum, sigma=self.smooth_slider.value)

        if trace_freeze is False:
            if self.single_plot_button.value:
                self.line_plot.data = []

            self.line_plot.add_trace(
                go.Scatter(
                    x=self.wavelengths,
                    y=spectrum,
                    mode="lines",
                    name=f"X={self._cur_ix} Y={self._cur_iy}"
                )
            )
            self.line_plot.update_traces(hoverinfo="text+name", mode="lines")
            xlab_unit = self.display_unit.to_string()
            self.line_plot.update_layout(
                xaxis_title=f"wavelength [{xlab_unit}]",
                yaxis_title="fλ (1e-17 erg s⁻¹ cm⁻² Å⁻¹)"
            )

        # Vertical line at current slice wavelength
        x_vline = self.wavelengths[self._cur_islice]
        self.line_plot.layout.shapes = []  # clear previous vline
        self.line_plot.add_vline(x=x_vline, line_color="grey", line_width=2)

    def set_rainbow(self):
        try:
            wav_A = (self.wavelengths * self.display_unit).to(u.AA).value
            wmin, wmax = np.nanmin(wav_A), np.nanmax(wav_A)
            wgrid = np.linspace(wmin, wmax, 300)
            norm = plt.Normalize(wmin, wmax)
            colorlist = list(zip(norm(wgrid), [wavelength_to_rgb(w) for w in wgrid]))
            self.spectralmap = matplotlib.colors.LinearSegmentedColormap.from_list("spectrum", colorlist)
            self.clim = (wmin, wmax)
        except Exception:
            self.spectralmap = None
            self.clim = None

    def image_show_slice(self, n):
        self.image.set_naxispath([n])
        self._viewer.redraw(whence=0)
        self._cur_islice = int(n)
        self._update_wave_label()  # keep λ label in sync with displayed slice

    def show_slice(self, idx):
        idx = int(np.clip(idx, 0, self.nwave - 1))
        self.image_show_slice(idx)
        self.plot_spec(trace_freeze=True)  # refresh vline, keep existing traces
        self._update_wave_label()          # also update after slider/Play drives show_slice

    # ---------- helper: wavelength label ----------
    def _update_wave_label(self):
        """Show the current slice's wavelength above the 1D plot."""
        lam = float(self.wavelengths[int(getattr(self, "_cur_islice", 0))])
        unit = self.display_unit.to_string()
        self.wave_title.value = (
            f"<div style='font-size:22px; font-weight:600; line-height:1.1; "
            f"margin:0 0 6px 0;'>λ = {lam:.1f} {unit}</div>"
        )
