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

        self._cur_ix = None
        self._cur_iy = None
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
        self._internal_update = False  # guard to avoid feedback loops

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

        # === Editable wavelength box (above the plot) ===
        # Use Å symbol explicitly
        self.wave_label = widgets.HTML(
            value=f"<div style='font-size:22px; font-weight:600; margin:0;'>λ [Å]</div>"
        )
        # bounds/step inferred from axis
        self._wmin = float(min(self.wavelengths[0], self.wavelengths[-1]))
        self._wmax = float(max(self.wavelengths[0], self.wavelengths[-1]))
        self._wstep = float(abs(self.wavelengths[1] - self.wavelengths[0])) if self.nwave > 1 else 1.0
        self.wave_input = widgets.BoundedFloatText(
            value=round(float(self.wavelengths[self._cur_islice]), 1),  # one decimal
            min=self._wmin, max=self._wmax, step=self._wstep,
            layout=widgets.Layout(width='220px')
        )
        self.wave_input_box = widgets.HBox([self.wave_label, self.wave_input],
                                           layout=widgets.Layout(align_items='center', gap='8px'))

        def _on_wave_input(change):
            if self._internal_update or change['name'] != 'value':
                return
            self._internal_update = True
            try:
                w = float(change['new'])
                n = int(np.argmin(np.abs(self.wavelengths - w)))  # snap to nearest plane
                self.idx_widget.value = n  # triggers show_slice via interactive link
                self.wave_input.value = round(float(self.wavelengths[n]), 1)
            finally:
                self._internal_update = False

        self.wave_input.observe(_on_wave_input, names='value')

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

        # ---- Bottom-left: RA/Dec readout in degrees (always shown) ----
        self.coord_readout = widgets.HTML(value="")
        # Layout
        left_panel = widgets.VBox([
            widgets.HBox([self.idx_widget, self.scan]),
            self,
            self.coord_readout,  # bottom-left readout
        ])
        right_panel = widgets.VBox([self.wave_input_box, self.line_plot, self.smooth_slider, self.single_plot_button])
        self.all_box = widgets.HBox([left_panel, right_panel])
#        display(self.all_box)

        # Initialize readouts
        self._update_wave_input()
        self._update_coord_readout()

        # Observers
        self.smooth_slider.observe(self.plot_spec, names='value')

        #display(self.all_box)  # add back at the very end

    def _ipython_display_(self, **kwargs):
        display(self.all_box)    
        
    def load_nddata(self, nddata, n=0):
        self.image = AstroImage()
        self.image.load_nddata(nddata, naxispath=[n])
        self._viewer.set_image(self.image)
        

    def _mouse_click_cb(self, viewer, event, data_x, data_y):
        self._cur_ix = int(round(data_x))
        self._cur_iy = int(round(data_y))
        # Plot first so the new line gets added (and we can grab its color)
        self.plot_spec()

        if self.single_plot_button.value:
            self.reset_markers()
        
        if self._cur_ix is not None and self._cur_iy is not None:
            mrk_tab = Table(names=["x", "y"])
            mrk_tab.add_row([self._cur_ix, self._cur_iy])
            spec_color = getattr(self, "_last_trace_color", "#FF0000")  # fallback red
            self.marker = {
                "color": spec_color,
                "radius": 2,     # still controls the circle size
                "width": 3,      # <-- NEW: outline/line thickness
                "type": "circle"
            }
            self.add_markers(mrk_tab)

        self._update_coord_readout()

    
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
        
            hover_tmpl = (
                "λ = %{x:.1f} Å<br>"
                "fλ = %{y:.4g} (1e-17 erg s⁻¹ cm⁻² Å⁻¹)"
                "<extra></extra>"
            )
        
            line_color = self._get_next_trace_color()
            self.line_plot.add_trace(
                go.Scatter(
                    x=self.wavelengths,
                    y=spectrum,
                    mode="lines",
                    name="",
                    hovertemplate=hover_tmpl,
                    line=dict(color=line_color),  # <-- set explicit color
                )
            )
            # Remember for the matching image marker
            self._last_trace_color = line_color
        
            self.line_plot.update_traces(mode="lines")
            self.line_plot.update_layout(
                xaxis_title="wavelength [Å]",
                yaxis_title="fλ (1e-17 erg s⁻¹ cm⁻² Å⁻¹)"
            )


        # Vertical line at current slice wavelength
        x_vline = self.wavelengths[self._cur_islice]
        self.line_plot.layout.shapes = []  # clear previous vline
        self.line_plot.add_vline(x=x_vline, line_color="grey", line_width=2)

    def _get_next_trace_color(self):
        # Use explicit colorway so we know the exact hex values
        colorway = (list(self.line_plot.layout.colorway)
                    if getattr(self.line_plot.layout, "colorway", None)
                    else ['#636EFA','#EF553B','#00CC96','#AB63FA','#FFA15A',
                          '#19D3F3','#FF6692','#B6E880','#FF97FF','#FECB52'])
        idx = len(self.line_plot.data)  # index of the trace we’re about to add
        return colorway[idx % len(colorway)]

        
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
        self._update_wave_input()
        self._update_coord_readout()

    def show_slice(self, idx):
        idx = int(np.clip(idx, 0, self.nwave - 1))
        self.image_show_slice(idx)
        self.plot_spec(trace_freeze=True)  # refresh vline, keep existing traces

    # ---------- helpers ----------
    def _update_wave_input(self):
        """Update the editable wavelength textbox from current slice, rounding to 0.1."""
        if not hasattr(self, "wave_input"):
            return
        val = round(float(self.wavelengths[int(getattr(self, "_cur_islice", 0))]), 1)
        if self._internal_update:
            self.wave_input.value = val
        else:
            self._internal_update = True
            try:
                self.wave_input.value = val
            finally:
                self._internal_update = False

    def _update_coord_readout(self):
        """Update bottom-left readout with RA/Dec in degrees."""
        if not hasattr(self, "coord_readout"):
            return
        if self._cur_ix is None or self._cur_iy is None:
            self.coord_readout.value = "<span style='opacity:0.6'>click to show coordinates (deg)</span>"
            return
        try:
            ra, dec, _ = self.wcs.all_pix2world(
                np.array([self._cur_ix], dtype=float),
                np.array([self._cur_iy], dtype=float),
                np.array([self._cur_islice], dtype=float),
                0
            )
            self.coord_readout.value = f"<b>RA</b> = {ra[0]:.6f}° &nbsp; <b>Dec</b> = {dec[0]:.6f}°"
        except Exception:
            self.coord_readout.value = "<span style='opacity:0.6'>WCS conversion failed</span>"
