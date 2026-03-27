import lime
from specsy import extinction_coeff_calc
from utils.plots import extinction_gradient


lines_df = lime.load_frame(f'/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Online_example_data/SHOC579_measurements.txt')
lime.theme.default_lib = 'bokeh'
# cHbeta, cHbeta_err, log_extinc = extinction_coeff_calc(lines_df, 'H1_4861A', plot_results=True)
# print(cHbeta, cHbeta_err)

cHbeta, cHbeta_err, log_extinc = extinction_coeff_calc(lines_df, 'H1_6563A', plot_results=False, rel_Hbeta=False)
print(cHbeta, cHbeta_err)


extinction_gradient(cHbeta, cHbeta_err, lines_df, rel_Hbeta=True)



# def extinction_test():
#
#     lines_df = load_frame(f'/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Online_example_data/SHOC579_measurements.txt')
#
#     cHbeta, cHbeta_err, log_extinc = extinction_coeff_calc(lines_df, 'H1_4861A', plot_results=True)
#
#     print(cHbeta, cHbeta_err)
#
#     return
#
# if main ==