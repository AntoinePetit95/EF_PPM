import os
import streamlit as st


help_outil = ("**Parcellaire PM** est un outil gratuit conçu par **Énergie Foncière** pour simplifier "
              "l’exploitation des fichiers annuels de parcelles détenues par des personnes morales. "
              "À partir d’une parcelle ou d’une liste de références cadastrales, il permet d’identifier "
              "les propriétaires concernés puis d’exporter les résultats.")


with st.sidebar:
    logo_path = f".{os.sep}EF_PPM{os.sep}assets{os.sep}LOGO-EF-RVB.svg"
    st.logo(logo_path, size='large', link='https://energie-fonciere.fr/')
    st.title("Parcellaire PM", help=help_outil)
    st.caption("Le foncier des personnes morales, simplement !")
    bas_de_page = st.container(vertical_alignment='bottom')
    bas_de_page.caption("Données : septembre 2025")

pages = {
    "Demande": [
        st.Page("page_par_parcelle.py", title="Par parcelle"),
        st.Page("page_par_siren.py", title="Par SIREN"),
        st.Page("page_par_nom.py", title="Par nom")
    ],
    "Ressources": [
        st.Page("page_readme.py", title="Lisez-moi"),
    ]
}

pg = st.navigation(pages, position="top")
pg.run()

