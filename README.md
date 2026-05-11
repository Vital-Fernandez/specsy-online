# Specsy Online

<p align="center">
  <img src="https://github.com/Vital-Fernandez/specsy/blob/7e35568f6d154486f5603e94fe39dd08e5e54834/src/specsy/resources/images/Specsy_logo_transparent_dark.PNG" alt="Specsy Logo" width="300"/>
</p>

Streamlit wrapper for [SpecSy](https://github.com/Vital-Fernandez/specsy) — a Python library for astrophysical spectral analysis.

## Installation

This command will install the main [Aspect](https://github.com/Vital-Fernandez/aspect), [LiMe](https://github.com/Vital-Fernandez/lime), and [Specsy](https://github.com/Vital-Fernandez/specsy) libraries alongside their main dependencies.

```bash
pip install specsy-online
```

Depending on the operating system, the selection of the PyMC sampler backend for the chemical analysis may have a dramatic impact on the compilation speed of the sampler.
It is recommended to use conda to create an environment with the recommended backends:

```bash
conda create -c conda-forge -n specsy_online python=3.13 nutpie pymc numba numpyro blackjax
conda activate specsy_online
pip install specsy-online
```

To upgrade to the latest version:

```bash
pip install --upgrade specsy-online
```

## Usage

Launch the browser interface based on Streamlit by running on the terminal:

```bash
specsy
```

## Development

This wrapper is in an alpha development phase. Please contact the author for any issues.

Vital Fernández — [vgf@stsci.edu](mailto:vgf@stsci.edu)