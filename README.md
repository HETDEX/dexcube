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
| 02    | **02-DownloadingCubes.ipynb**              | Authenticating and fetching cubes in bulk          | How to download and decompress FITS cubes.                                                                      |
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

## 🐳 Docker Setup

If you prefer a fully self-contained environment you can run all notebooks inside a Docker container. Two options are provided.

### A) Run the pre-built image (recommended). The PDR1 products will be downloaded into the directory $PWD/pdr1, and will be located in work directory within the container.

```bash
docker run --pull always -p 8888:8888 -v "$PWD":/home/jovyan/work -it hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token='' \
  --ServerApp.root_dir=/home/jovyan \
  --ServerApp.default_url=/lab/tree/work/README.md

```

The server prints a URL with a token; open it in your browser (usually `http://localhost:8888`).  
Your current directory is mounted inside the container as `/workspace`, so any changes you make to notebooks or data persist on your host.

### B) Build a local image from this repo

```bash
$ git clone https://github.com/HETDEX/dexcube.git
$ cd dexcube
# build the image (takes ~5 min the first time)
$ docker build -t dexcube:latest .

# run it exactly as above
$ docker run -it --rm -p 8888:8888 -v "$PWD":/home/jovyan/work -it hetdex/dexcube:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token='' \
  --ServerApp.root_dir=/home/jovyan \
  --ServerApp.default_url=/lab/tree/work/README.md
```

Feel free to edit the provided **Dockerfile** to pin package versions or add extra libraries.

---

## 🤝 Contributing & Support

- Pull requests are welcome – please open an Issue first if you plan major changes.  
- If something breaks, raise a GitHub Issue with the notebook name and the cell that failed.  

Released under the MIT License.  
© 2025 HETDEX Collaboration.
