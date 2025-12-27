import streamlit as st

from EF_PPM.retriever.retriever import PPM
from EF_PPM.utils.dept_code import DEPARTEMENTS_CODES, DEPARTEMENTS

@st.fragment
def affiche_tableau(ppm:PPM) -> None:

    ppm_to_show = ppm

    help_suf = ("La **subdivision fiscale (suf)** est une partie de parcelle ayant la même nature de culture "
                "(c’est-à-dire la même affectation fiscale). Il est très rare que les SUF d'une même parcelle "
                "aient des propriétaires différents, il est conseillé de les regrouper pour une lecture plus simple.")
    group_by_suf = st.toggle("Grouper les SUF", help=help_suf, value=True)
    if group_by_suf:
        ppm_to_show = ppm_to_show.merged_suf

    help_rights = "Grouper les informations des ayants-droits pour avoir une seule ligne par parcelle."
    group_by_rights = st.toggle("Grouper les droits", help=help_rights, value=False)
    if group_by_rights:
        ppm_to_show = ppm_to_show.merged_rights

    help_essential = "Ne conserver que les informations essentielles."
    show_only_essential = st.toggle("Fichier simplifié", help=help_essential, value=True)
    if show_only_essential:
        ppm_to_show = ppm_to_show.essential

    ppm_to_show.sort_by_idu()
    st.write(ppm_to_show.table)

    st.download_button(
        "Télécharger la table",
        data=ppm_to_show.excel_file_bytes,
        mime="application/octet-stream",
        file_name="Énergie_Foncière_parcellaire_PM.xlsx"
    )


def initialize_values() -> None:
    values = {
        'nom': None,
        'mode': 'exact',
        'departements': [],
        'ppm_nom': PPM(),
    }
    for k, v in values.items():
        if k not in st.session_state.keys():
            st.session_state[k] = v

initialize_values()

st.title("Recherche par nom")

def interroge_base() -> None:
    if not st.session_state['nom']:
        return
    if not st.session_state['departements']:
        return

    with st.spinner("Récupération des informations ...", show_time=True):
        ppm = PPM()
        ppm.fetch_name(
            name=st.session_state['nom'].upper(),
            limit_to_department=st.session_state['departements'],
            mode=st.session_state['mode']
        )
        st.session_state['ppm_nom'] = ppm
    st.success("Informations récupérées !")

    affiche_tableau(st.session_state['ppm_nom'])

tab_nom, tab_departements = st.tabs(['Nom', 'Départements'])



with tab_nom:
    st.text_input("Dénomination de la personne morale", "PARIS", key='nom')

    options = {
        "exact": "Correspondance exact",
        "contains": "Contient",
    }
    format_function = lambda x: options[x]

    st.pills("Mode", options=options.keys(), format_func=format_function, key='mode')

    nom_est_correct = True

    if st.session_state['nom'] is None:
        st.warning('Entrez un nom')
        nom_est_correct = False
    elif not len(st.session_state['nom']) >= 2:
        st.warning('Entrez au moins 2 caractères')
        nom_est_correct = False

    disabled = not nom_est_correct

    if not nom_est_correct:
        disabled = True

    if not st.session_state['departements']:
        st.warning("Il n'y a pas de départements")
        disabled = True

    if len(st.session_state['departements']) >= 3:
        st.warning(f'Beaucoup de départements ont été sélectionnés, la recherche prendra environ '
                   f'{len(st.session_state["departements"]) * 4} secondes')
    bouton_interroger = st.button(
        label="interroger la base",
        disabled=disabled,
        type='primary'
    )

    if bouton_interroger:
        interroge_base()

with tab_departements:
    def format_function(dept_code: str) -> str:
            return f"{dept_code} - {DEPARTEMENTS[dept_code]}"

    st.multiselect(
        "A quels départements limiter la recherche ?",
        DEPARTEMENTS_CODES,
        default=st.session_state['departements'],
        format_func=format_function,
        key='departements'
    )

