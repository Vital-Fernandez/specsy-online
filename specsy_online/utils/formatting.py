REGION_TAGS_STYLE = """
                    <style>
                    .region-card {
                        border: 1px solid #30363d;
                        border-radius: 10px;
                        padding: 1.2rem 1.4rem 1rem;
                        margin-bottom: 1rem;
                        position: relative;
                    }
                    .region-card::before {
                        content: '';
                        position: absolute;
                        top: 0; left: 0;
                        width: 4px; height: 100%;
                        border-radius: 10px 0 0 10px;
                    }
                    .region-low::before    { background: #C41E3A; }
                    .region-med::before    { background: #f78166; }
                    .region-high::before   { background: #FFDB58; }
                    .region-vhigh::before  { background: #58a6ff; }
                    .region-region::before { background: #ffa657; }
                    </style>
                    """

REGION_TAGS_COLORS = {"low": "#C41E3A", "med": "#f78166", "high": "#FFDB58", "vhigh": "#58a6ff"}


REGION_LABELS = {1: ["low"],
                 2: ["low", "high"],
                 3: ["low", "med", "high"],
                 4: ["low", "med", "high", "vhigh"]}

COLUMNS_STRUCT = ['line_flux', 'line_flux_err', 'region', 'particle', 'merged', 'norm_line', 'f_lambda',
                  'temp', 'den', 'eq_temp', 'eq_den', 'eq_flux']


CODE_ARRAYS_OBSERVATION = """
import lime
import numpy as np

spec = lime.Spectrum(
    input_wave=wave,
    input_flux=flux,
    input_err=err,
    redshift=0.0132,
    units_wave="AA",
    units_flux="FLAM",
)
"""

CODE_FROM_FILE_OBSERVATION = """
import lime
import numpy as np

# OSIRIS spectrum with redshift
spec = lime.Spectrum.from_file("osiris_obs.fits", instrument="osiris", redshift=0.013)

# SDSS spectrum masking NaN and negative pixels
spec = lime.Spectrum.from_file("spec-12345.fits", instrument="sdss",
                                pixel_mask=[np.nan, "negative"])

# ISIS spectrum with normalization and wavelength crop
spec = lime.Spectrum.from_file("isis_star.fits", instrument="isis",
                                norm_flux=1e-16, crop_waves=(4000, 7000))
"""

CODE_LINES_FRAME_BASIC = """
import lime

# Get all lines in the spectrum wavelength range
bands = spec.retrieve.lines_frame()
"""

CODE_LINES_FRAME_FILTERED = """
import lime

# Restrict to hydrogen and oxygen transitions with a wider velocity band
bands = spec.retrieve.lines_frame(particle_list=["H1", "O3"], band_vsigma=120)

# Read the bands configuration from a configuration file
bands = spec.retrieve.lines_frame(fit_cfg="./my_cfg.toml")
"""

CODE_LINES_FRAME_ADVANCED = """
import lime

# Per-line velocity sigma overrides
bands = spec.retrieve.lines_frame(
    band_vsigma=70,
    map_band_vsigma={"O3_5007A": 150, "H1_6563A": 200},
    exclude_bands_masked=True,
    vacuum_waves=False,
)
"""


CODE_FIT_FRAME_BASIC = """
import lime

# Measure all lines from a bands file
spec.fit.frame("my_bands.txt", fit_cfg="my_fit_config.toml")

# Measure all lines from a bands dataframe without a progress bar
spec.fit.frame(bands_df, progress_output=None)
"""

CODE_FIT_FRAME_FILTERED = """
import lime

# Limit to a subset of lines
spec.fit.frame(bands_df, line_list=["O3_5007A", "H1_4861A"])

# Change the default profile and shape
spec.fit.frame(bands_df, min_method="leastsq", profile="l", shape="abs")
"""

CODE_FIT_FRAME_ADVANCED = """
import lime

# Enable automatic line detection from the continuum fitting parameters from the .toml configuration
spec.fit.frame(bands_df, line_detection=True, fit_cfg="my_fit_config.toml")

# Use the adjacent bands for both the flux uncertainty and the linear continuum source. 
spec.fit.frame(bands_df, cont_source="adjacent", err_from_bands=True)
"""




# def card_formating(label):
#     msg = (f'<div class="region-card region-{label}">'
#            f'<p style="color:{REGION_TAGS_COLORS[label]};font-size:0.75rem;font-weight:600;'
#            f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">'
#            f'Region · {label.upper()}</p>')
#
#     return msg


def card_formating(label):
    msg = (f'<div class="region-card region-{label}">'
           f'<p style="color:{REGION_TAGS_COLORS[label]};font-size:0.75rem;font-weight:600;'
           f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">'
           f'Region · {label.upper()}</p>'
           f'</div>')
    return msg