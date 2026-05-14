import streamlit as st
from specsy_online.utils.input_output import load_logo, get_versions, get_sampler_backends, get_device_info
from specsy_online.utils.sidebar import sidebar_widgets


# Sidebar
sidebar_widgets()

# Url menus
st.set_page_config(page_title="SpecSy", menu_items={'Report a bug': "https://github.com/Vital-Fernandez/specsy"},
                   layout='wide')

# Specsy logo and welcome
col_logo, col_welcome = st.columns([0.4, 0.6], gap='large')
with col_logo:
    st.image(load_logo(), width=300)

with col_welcome:
    st.markdown(f'# SpecSy')

# Introduction text
st.space('medium')
st.markdown("""
                <p style='font-size:20px;'>
                Welcome to the Spectra Synthesis platform.
                Use the sidebar menu to navigate the tools.
                </p>
                """, unsafe_allow_html=True)

# Installation
with st.expander("Offline installation", icon=":material/download:"):
    st.markdown(
        """
        This command will install the main [Aspect](https://github.com/Vital-Fernandez/aspect), 
        [LiMe](https://github.com/Vital-Fernandez/lime), and 
        [Specsy](https://github.com/Vital-Fernandez/specsy) libraries alongside their main dependencies.
        """
    )
    st.code("pip install specsy-online", language="bash")

    st.markdown(
        """
        Depending on the operating system, the selection of the PyMC sampler backend for the chemical 
        analysis may have a dramatic impact on the compilation speed of the sampler.  
        It is recommended to use conda to create an environment with the recommended backends installation and test for
        the best option:
        """
    )
    st.code(
        """
conda create -c conda-forge -n specsy_online python=3.13 nutpie pymc numba numpyro blackjax
conda activate specsy_online
pip install specsy-online
        """,
        language="bash"
    )

    st.markdown("To upgrade to the latest version:")
    st.code("pip install --upgrade specsy-online", language="bash")

# References
with st.expander("Tools references", icon=":material/handyman:"):
    st.markdown(
        """
        **(LiMe) Fernández, V., Morisset, C., & Hernández, S. (2024).**  
        *[LIME: A LIne MEasuring library for large and complex spectroscopic datasets.](https://www.aanda.org/articles/aa/full_html/2024/08/aa49224-24/aa49224-24.html)*  

        **(SpecSy) Fernández, V., Amorín, R., Sánchez-Janssen, R., del Valle-Espinosa, M. G., & Papaderos, P.(2023).**   
        *[The resolved chemical composition of the starburst dwarf galaxy CGCG007-025: direct method versus
         photoionization model fitting.](https://doi.org/10.1093/mnras/stad198)*  
        """,

        unsafe_allow_html=True
    )

with st.expander("Data references", icon=":material/import_contacts:"):
    st.markdown(
        """
        **(PyNeb) Luridiana, V., Morisset, C., & Shaw, R. A.(2015).**   
        *[PyNeb: A new tool for analyzing emission lines.](https://www.aanda.org/articles/aa/full_html/2015/01/aa23152-13/aa23152-13.html)*  

        **Chatzikos, M., Bianchi, S., Camilloni, F., et al. (2023).**  
        *[The 2023 release of Cloudy.](https://arxiv.org/abs/2308.06396)*  
        """,

        unsafe_allow_html=True)

with st.expander("Dependencies installed", icon=":material/package_2:"):
    versions = get_versions()
    cols = st.columns(3)
    for i, (label, version) in enumerate(versions.items()):
        cols[i % 3].metric(label=label, value=f"v{version}")

with st.expander("Sampler backends", icon=":material/tune:"):
    backends = get_sampler_backends()
    cols = st.columns(3)
    for i, (pkg, version) in enumerate(backends.items()):
        if version:
            cols[i % 3].metric(label=pkg, value=f"v{version}")
        else:
            cols[i % 3].metric(label=pkg, value="unavailable", delta="not installed", delta_color="off")

    st.divider()
    device_info = get_device_info()
    cpu_col, jax_col, pytensor_col, cuda_col = st.columns(4)
    cpu_col.metric(label="CPU cores", value=device_info["cpu_cores"])
    if device_info.get("jax_backend"):
        jax_label = f"JAX ({', '.join(device_info['jax_devices'])})"
        jax_col.metric(label="JAX backend", value=device_info["jax_backend"], help=jax_label)
    else:
        jax_col.metric(label="JAX backend", value="unavailable", delta="not installed", delta_color="off")
    if device_info.get("pytensor_device"):
        pytensor_col.metric(label="PyTensor device", value=device_info["pytensor_device"],
                            help=f"floatX: {device_info['pytensor_floatX']}")
    else:
        pytensor_col.metric(label="PyTensor device", value="unavailable", delta="not installed", delta_color="off")
    cuda_col.metric(
        label="CUDA (numba)",
        value="available" if device_info["cuda_available"] else "unavailable",
        delta=None,
        delta_color="off" if not device_info["cuda_available"] else "normal"
    )

    jax_devices_col, _ = st.columns([0.25, 0.75])
    try:
        import jax
        jax_devices_col.metric(label="JAX device count", value=jax.local_device_count(),
                               help="Set with `numpyro.set_host_device_count(os.cpu_count())` before importing JAX")
    except Exception:
        jax_devices_col.metric(label="JAX device count", value="unavailable", delta="not installed", delta_color="off")

