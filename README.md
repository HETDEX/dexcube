# 🌌 HETDEX Public Data Release — Cube Tutorial

![CubeWidget demo](notebooks/cubewidget-demo.gif)

Welcome to **dexcube**: a hands-on set of Jupyter notebooks that teach you how to *find, download, and analyse* the 3-D IFU (Integral Field Unit) datacubes in the HETDEX Public Data Release (PDR 1).

These notebooks are meant to be opened sequentially – each one builds on the skills and files created in the previous step. In a couple of hours you will go from an empty working directory to:

- a local subset of PDR cubes  
- interactive visual exploration of flux, variance and metadata  
- extraction of 1D spectra
- generation of 2D line flux maps
- access to the official HETDEX Source Catalog  
- quick source look-up and cross-matching to external catalogues  
- scaling up to batch downloads and large-catalog extractions  

---

## 🗂 Notebook Guide

| Order | Notebook                                   | What it covers                                     | Key take-aways                                                                                                  |
| ----- | ------------------------------------------ | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 01    | **01-DataModel+IFU-Index.ipynb**           | PDR data model & the master IFU index FITS file    | Understand cube filenames, sky coverage and the columns you will use for programmatic searches.                 |
| 02    | **02-DownloadingCubes.ipynb**              | Authenticating and fetching cubes in bulk          | How to download FITS cubes.                                                                      |
| 03    | **03-DataCubeFormat.ipynb**                | Anatomy of a single cube                           | What’s in the 3 HDU extensions (DATA, ERROR, BITMASK); units; header keywords.                                  |
| 04    | **04-MaskingOptions.ipynb**                | Quality & science masks                            | Build boolean masks from BITMASK bits.                                                                          |
| 05    | **05-CubeWidget.ipynb**                    | Interactive exploration                            | A lightweight `CubeWidget` for browsing xyλ slices, clicking spaxels to see spectra, adjusting display scaling. |
| 06    | **06-CoordinateQuery.ipynb**               | Sky-coordinate searches                            | Given an RA/Dec list, locate covering cubes/IFUs, open them, and overlay reference catalogues.                  |
| 07    | **07-CollapsingCubes.ipynb**               | Creating 2-D images                                | Collapse along wavelength to make white-light or narrow-band maps; write the result as a FITS image.            |
| 08    | **08-ExtractingSpectra.ipynb**             | 1-D spectral extraction                            | Example 1D spectral extraction, continuum subtraction and per-pixel error propagation.                          |
| 09    | **09-CatalogExtractions.ipynb**            | Batch 1D extractions from a source catalog         | Extract spectra on many cubes, compile an Astropy Table, and save as ECSV/FITS.                                 |
| 10    | **10-HETDEX-Source-Catalog.ipynb**         | Exploring the HETDEX source catalog                | Learn the structure of the official catalog and how to cross-match to your extractions.                         |
| 11    | **11-Source-Look-Up.ipynb**                | Quick source look-up                               | Given coordinates or IDs, locate and open corresponding sources/cubes.                                          |
| 12    | **12-BatchDownloads-ForRemoteUsers.ipynb** | Scaling up for remote users                        | Download and stage multiple cubes efficiently for offline analysis.                                             |

> **Tip** Open the notebooks in JupyterLab and *Run All* one at a time. A small test cube is fetched automatically so you can experiment even without full-survey access.

---

## ⚡ Quick Start outside the public Jupyter Hub

```bash
# 1) clone & install
$ git clone https://github.com/HETDEX/dexcube.git
$ cd dexcube
$ pip install -r requirements.txt
```

The notebooks assume Python 3.10+, `astropy`, `numpy`, `matplotlib`, and `ipywidgets`.  
All required packages are listed in *requirements.txt*. Launch JupyterLab from the repo root:

```bash
$ jupyter lab notebooks/
```

---

## 🤖 LLM & Programmatic Access Context

For AI-assisted analysis, automated pipelines, or a quick orientation to the data
model, see [`HETDEX_CONTEXT.md`](./HETDEX_CONTEXT.md). It contains:

- Survey parameters, field coordinates, and sky coverage
- Complete datacube format (HDU structure, exact dimensions, units, WCS notes)
- Full bitmask table with recommended masking strategies
- IFU index file schema and a coordinate query code example
- HPSC2 source catalog column descriptions
- Data paths for all access environments (JupyterHub, TACC, Docker)
- Common errors and gotchas

If you are using Claude Code, Cursor, or another LLM coding assistant, the
[`CLAUDE.md`](./CLAUDE.md) file in this repo root is loaded automatically and
provides the critical facts needed to generate correct HETDEX analysis code.

---

## 🐳 Docker Setup

If you prefer a fully self-contained environment, run all notebooks inside a
Docker container. Two options are provided.

PDR1 data is downloaded to and read from `work/pdr1/` inside the container,
which maps to `./work/pdr1/` in your current directory on the host — matching
the path layout used on the TACC JupyterHub. Run the docker command from the
root of this cloned repo.

### A) Run the pre-built image (recommended)

**Linux / Intel Mac:**
```bash
docker run --pull always --rm -p 8888:8888 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''
```

**Apple Silicon Mac (M1/M2/M3/M4):**
```bash
docker run --pull always --rm -p 8888:8888 \
  --platform linux/amd64 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''
```

> The image is built for Linux/AMD64 to match the TACC JupyterHub environment.
> Apple Silicon Macs run it via Rosetta 2 emulation — it works correctly but
> requires the `--platform linux/amd64` flag.

Open the URL printed in the terminal (usually `http://127.0.0.1:8888`).
Any PDR1 data downloaded inside the container will persist in `./work/pdr1/`
on your host machine.

### B) Build a local image from this repo

```bash
git clone https://github.com/HETDEX/dexcube.git
cd dexcube

# Build the image (takes ~5 min the first time)
docker build --platform linux/amd64 -t dexcube:latest .

# Linux / Intel Mac
docker run --rm -p 8888:8888 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''

# Apple Silicon Mac
docker run --rm -p 8888:8888 \
  --platform linux/amd64 \
  -v "$PWD/work/pdr1":/home/jovyan/work/pdr1 \
  dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
  --NotebookApp.token=''
```

Feel free to edit the provided **Dockerfile** to pin package versions or add
extra libraries.

---

## 🤝 Contributing & Support

- Pull requests are welcome – please open an Issue first if you plan major changes.  
- If something breaks, raise a GitHub Issue with the notebook name and the cell that failed.  


## 📜 Acknowledgements

If you use HETDEX PDR1 data products in your research, please include the
following acknowledgement text and citations in your paper.

### Required Citations

- **HETDEX Survey**: Gebhardt et al. 2021, ApJ 923, 217 — [doi:10.3847/1538-4357/ac2e03](https://doi.org/10.3847/1538-4357/ac2e03)
- **VIRUS Instrument**: Hill et al. 2021, AJ 162, 298 — [doi:10.3847/1538-3881/ac2c02](https://doi.org/10.3847/1538-3881/ac2c02)
- **PDR1 Data Release**: Mentuch Cooper et al. 2026 (submitted) — [doi:10.5281/zenodo.19581262](https://doi.org/10.5281/zenodo.19581262)

For a full list of citation guidelines see [hetdex.org/papers](https://hetdex.org/papers/).

### Required Acknowledgement Text

> HETDEX is led by the University of Texas at Austin McDonald Observatory and
> Department of Astronomy with participation from the
> Ludwig-Maximilians-Universität München, Max-Planck-Institut für
> Extraterrestrische Physik (MPE), Leibniz-Institut für Astrophysik Potsdam
> (AIP), Texas A&M University, The Pennsylvania State University, Institut für
> Astrophysik Göttingen, The University of Oxford, Max-Planck-Institut für
> Astrophysik (MPA), The University of Tokyo, and Missouri University of Science
> and Technology.
>
> Observations for HETDEX were obtained with the Hobby-Eberly Telescope (HET),
> which is a joint project of the University of Texas at Austin, the Pennsylvania
> State University, Ludwig-Maximilians-Universität München, and
> Georg-August-Universität Göttingen. The HET is named in honor of its principal
> benefactors, William P. Hobby and Robert E. Eberly.
>
> The Visible Integral-field Replicable Unit Spectrograph (VIRUS) was used for
> HETDEX observations. VIRUS is a joint project of the University of Texas at
> Austin, Leibniz-Institut für Astrophysik Potsdam (AIP), Texas A&M University
> (TAMU), Max-Planck-Institut für Extraterrestrische Physik (MPE),
> Ludwig-Maximilians-Universität München, Pennsylvania State University, Institut
> für Astrophysik Göttingen, University of Oxford, and the Max-Planck-Institut
> für Astrophysik (MPA). In addition to institutional support, VIRUS was
> partially funded by the National Science Foundation, the State of Texas, and
> generous support from private individuals and foundations.


Released under the MIT License.  
© 2026 HETDEX Collaboration.
