import lime

fname = '/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Online_example_data/sdss_dr18_0358-51818-0504.fits'
bands = '/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Online_example_data/SHOC579_bands.txt'
cfg = '/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Online_example_data/shoc579_cfg.toml'

spec = lime.Spectrum.from_file(fname, instrument='sdss')
spec.fit.frame(bands, cfg)
spec.bokeh.spectrum()
spec.plot.grid()


from bokeh.io import output_file, show
from bokeh.layouts import gridplot
from bokeh.plotting import figure

output_file("layout_grid_convenient.html")

x = list(range(11))
y0 = x
y1 = [10 - i for i in x]
y2 = [abs(i - 5) for i in x]

# create three plots
s1 = figure(background_fill_color="#fafafa")
s1.circle(x, y0, size=12, alpha=0.8, color="#53777a")

s2 = figure(background_fill_color="#fafafa")
s2.triangle(x, y1, size=12, alpha=0.8, color="#c02942")

s3 = figure(background_fill_color="#fafafa")
s3.square(x, y2, size=12, alpha=0.8, color="#d95b43")

# make a grid
grid = gridplot([s1, s2, s3], ncols=2, width=250, height=250)

show(grid)

# from bokeh.models import Legend, LegendItem
# from bokeh.palettes import Category10_3
# from bokeh.plotting import figure, show
# from bokeh.sampledata.iris import flowers
# from bokeh.transform import factor_cmap, factor_mark
#
# SPECIES = ['setosa', 'versicolor', 'virginica']
# MARKERS = ['x', 'circle', 'triangle']
# STYLES = ['dotted', 'dashed', 'solid']
# labels_int = ["> 40% conf.", "> 60% conf.", "> 80% conf."]
# p = figure()
#
# # plot the actual data using factor and color mappers (using the same
# # column `species` here but you can use two different columns if you want)
# r = p.scatter("petal_length", "sepal_width", source=flowers, fill_alpha=0.4, size=12,
#               marker=factor_mark('species', MARKERS, SPECIES),
#               color=factor_cmap('species', Category10_3, SPECIES))
#
# # we are going to add "dummy" renderers for the legends, restrict auto-ranging
# # to only the "real" renderer above
# p.x_range.renderers = [r]
# p.y_range.renderers = [r]
#
# # create an invisible renderers to drive color legend
# rc = p.rect(x=0, y=0, height=1, width=1, color=Category10_3)
# rc.visible = False
#
# rs = p.scatter(x=0, y=0, color="grey", marker=MARKERS)
# rs.visible = False
#
#
#     # Add corresponding text
#     # p.text(x=[5.6], y=[y], text=[label], text_font_size="10pt", text_baseline="middle")
#
#
# # rl = p.step(x=0, y=0, color="black", line_dash='dotted')
# # rl.visible = False
# # rl = p.step(x=0, y=0, color="black", line_dash='dashed')
# # rl.visible = False
# # rl = p.step(x=0, y=0, color="black", line_dash='solid')
# # rl.visible = False
#
# # Items of the legends
# items_legend1 = [LegendItem(label=SPECIES[i], renderers=[rc], index=i) for i, c in enumerate(Category10_3)]
# items_legend2 = [LegendItem(label=MARKERS[i], renderers=[rs], index=i) for i, s in enumerate(MARKERS)]
# # items_legend3 = [LegendItem(label=STYLES[i], renderers=[rlines[i]]) for i in range(len(STYLES))]
#
# # Add the legends color legend with explicit index, set labels to fit your need
# p.add_layout(Legend(items=items_legend1, location="top_center"))
# p.add_layout(Legend(items=items_legend2, location="top_right"))
# # p.add_layout(Legend(items=items_legend3, location="top_left"))
#
# # Plot dummy lines for the manual legend
# rlines = [None]
# for dash in STYLES:
#     rl = p.line(x=0, y=0, line_color="black", line_dash=dash, line_width=2)
#     rl.visible = False
#     rlines.append(rl)
#
#
# style_legend = Legend(items=[LegendItem(label=label, renderers=[r]) for label, r in zip(labels_int, rlines)],
#                       orientation="horizontal", location="center")
#
# # Add legend *below* the plot
# p.add_layout(style_legend, 'below')
#
# show(p)
