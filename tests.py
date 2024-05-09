import lime
import specsy
from pathlib import Path

lime.theme.set_style('dark')

specfile = '/home/vital/Desktop/sdss_dr18_0358-51818-0504.fits'
bands_file = '/home/vital/Desktop/SCHO579_bands.txt'
conf_file = '/home/vital/Desktop/cfg.toml'
results_file = '/home/vital/Desktop/SHOC579_results.txt'
emissivity_file = './resources/data/emissivity_db.nc'
output_db = './results/measurements.nc'

spec = lime.Spectrum.from_file(specfile, instrument='sdss')
spec.plot.spectrum(rest_frame=True)
# spec.check.bands(bands_file)
spec.fit.frame(bands_file, conf_file)
spec.plot.spectrum()
spec.save_frame(results_file)

# spec.infer.bands()
# z_fit = spec.infer.redshift(detection_bands='line_2d_pred')
# spec.update_redshift(z_fit)
#
# fig_cfg = {'figure.figsize': (16, 4),
#            'figure.dpi': 300,
#            "axes.titlesize" : 16,
#             "axes.labelsize" : 15,
#             "legend.fontsize" : 7,
#             "xtick.labelsize" : 10,
#             "ytick.labelsize" : 10,
#             "font.size" : 5}
# ax_cfg = {'title': 'SHOC579, SDSS observation'}
# output_plot ='/home/vital/Dropbox/Astrophysics/Seminars/Univap_2024/detection_spectrum.png'
# spec.plot.spectrum(rest_frame=True, detection_band='line_2d_pred', fig_cfg=fig_cfg, ax_cfg=ax_cfg)
#                    #output_address=output_plot)

# # spec.plot.spectrum(detection_band='line_2d_pred')
# line_bands = lime.line_bands(spec)
# # spec.check.bands(bands_file)
# spec.fit.frame(bands_file, conf_file)
# spec.plot.spectrum()

# spec = lime.Spectrum.from_file(specfile, instrument='sdss', redshift=0.047004700470047005)
# spec.fit.frame(bands_file, conf_file)
# spec.plot.spectrum(rest_frame=True)
# spec.save_frame(results_file)


# # Create a database with emissivity grids
# lines_db = lime.line_bands((3000, 10000))
# lines_db['norm_line'] = 'H1_4861A'
# lines_db['group_label'] = 'none'
# lines_db.loc['O2_3726A_m'] = lines_db.loc['O2_3726A']
# lines_db.loc['O2_3726A_m', 'wavelength'] = 3726.0300
# lines_db.loc['O2_3726A_m', 'group_label'] = "O2_3726A+O2_3729A"
# lines_db.loc['O2_7319A_m'] = lines_db.loc['O2_7319A']
# lines_db.loc['O2_7319A_m', 'wavelength'] = 7318.8124
# lines_db.loc['O2_7319A_m', 'group_label'] = "O2_7319A+O2_7330A"
# emiss_dict = sy.models.emissivity.generate_emis_grid(lines_db, norm_header='norm_line')
# save_grids(emissivity_file, emiss_dict)

# Load lines observations
log = specsy.load_frame(results_file, lines_list=None, flux_type='profile', norm_line='H1_4861A')
#
# Load emissivity grids and generate the interpolators
emiss_db = specsy.Innate(emissivity_file, x_space=[9000, 20000, 251], y_space=[1, 600, 101])

# Declare model
dm_twoTemps = specsy.models.DirectMethod(emiss_grids=emiss_db, R_v=3.4, extinction_law="G03 LMC",
                                         temp_low_diag='Hagele_2006')

# Declare model
line_list = ['O2_3726A', 'O2_3729A', 'H1_4340A', 'O3_4363A', 'O3_4959A', 'O3_5007A', 'S3_6312A', 'H1_6563A', 'S2_6716A',
             'S2_6731A']
dm_twoTemps.fit.frame(log, lines_list=line_list, output_folder='./results/', results_label='SHOC579')

# Plot the results
results_address = f'./results/SHOC579_infer_db.nc'
specsy.plots.plot_traces(results_address, f'./results/SHOC579_traces.png')
specsy.plots.plot_flux_grid(results_address, f'./results/SHOC579_flux_posteriors.png')
specsy.plots.plot_corner_matrix(results_address, f'./results/SHOC579_corner_matrix.png')

print(f'Finished')
