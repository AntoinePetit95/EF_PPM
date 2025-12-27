import streamlit as st
import pandas as pd

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
        'SIRENS': [],
        'departements': [],
        'ppm_siren': PPM(),
    }
    for k, v in values.items():
        if k not in st.session_state.keys():
            st.session_state[k] = v

initialize_values()

info_recherche_pm = ("La recherche par numéro SIREN peut être incomplète, "
                     "certains numéros SIREN de la base correspondent à une numérotation interne des impôts")
st.title("Recherche par numéro SIREN", help=info_recherche_pm)


def interroge_base() -> None:
    if not st.session_state['SIRENS']:
        return
    if not st.session_state['departements']:
        return
    with st.spinner("Récupération des informations ...", show_time=True):
        ppm = PPM()
        ppm.fetch_sirens(st.session_state['SIRENS'], limit_to_department=st.session_state['departements'])
        st.session_state['ppm_siren'] = ppm
    st.success("Informations récupérées !")

    affiche_tableau(st.session_state['ppm_siren'])

def supprimer_siren(_siren: str) -> None:
    if _siren in st.session_state['SIRENS']:
        st.session_state['SIRENS'].remove(_siren)


tab_pm, tab_fichier, tab_liste_pm, tab_departements, tab_resultats = st.tabs([
    'Ajouter une personne morale',
    'Importer un fichier',
    f'Numéros SIREN de la demande',
    f'Départements',
    'Résultats'],
)



with tab_pm:
    siren_input = st.text_input("Numéro SIREN", "519587851")

    siren_est_correct = True

    siren = str(siren_input)

    if not len(siren) >= 9:
        st.warning('le numéro SIREN doit être au moins sur 9 caractères')
        siren_est_correct = False

    bouton_ajouter_siren = st.button(
        label='ajouter à la demande',
        disabled=not siren_est_correct,
        type='primary'
    )

    if bouton_ajouter_siren:
        if siren not in st.session_state['SIRENS']:
            st.session_state['SIRENS'].append(siren)
            st.session_state['parcelles'].sort()
        st.rerun()
    st.caption(
        f"Demande actuelle : {len(st.session_state['SIRENS'])} SIREN "
        f"dans {len(st.session_state['departements'])} départements",
        text_alignment='right'
    )

with tab_fichier:
    fichier = st.file_uploader("Importer des numéro SIREN depuis un fichier excel", type=['xlsx', 'xls'])

    if fichier:
        excel_file = pd.ExcelFile(fichier)
        if len(excel_file.sheet_names) > 1:
            onglet = st.selectbox("plusieurs onglets existent. Lequel choisir ?", excel_file.sheet_names)

        onglet_df = pd.read_excel(fichier, sheet_name=onglet)

        with st.expander("aperçu de l'onglet"):
            st.write(onglet_df)

        if len(onglet_df.columns) > 1:
            col = st.selectbox("Quelle colonne contient les numéros SIREN ?", onglet_df.columns)

        liste_siren = onglet_df[col].dropna().to_list()
        liste_siren = [siren for siren in liste_siren if siren]  # remove None
        liste_siren = [siren for siren in liste_siren if len(siren) >= 9]

        with st.expander("aperçu des numéros SIREN"):
            st.write(pd.DataFrame(liste_siren))

        if not liste_siren:
            caption = "pas de numéros SIREN"
        else:
            caption = f"ajouterles numéros SIREN"

        bouton_ajouter_sirens_depuis_fichier = st.button(
            label=caption,
            disabled=not liste_siren,
        )

        if bouton_ajouter_sirens_depuis_fichier:

            st.session_state['SIRENS'].extend(liste_siren)
            st.session_state['SIRENS'] = list(set(st.session_state['SIRENS']))
            st.session_state['SIRENS'].sort()
            st.rerun()
    st.caption(
        f"Demande actuelle : {len(st.session_state['SIRENS'])} SIREN "
        f"dans {len(st.session_state['departements'])} départements",
        text_alignment='right'
    )

with tab_liste_pm:
    bouton_vider_liste = st.button(
        label="Vider la liste des numéros SIREN",
        disabled=not st.session_state['SIRENS'],
        type='primary',
        width='stretch'
    )

    if bouton_vider_liste:
        st.session_state['SIRENS'] = []
        st.rerun()

    for this_siren in st.session_state['SIRENS']:
        c_bout, c_siren = st.columns([1, 20], vertical_alignment='center', gap=None)
        c_bout.button(":x:", on_click=supprimer_siren, args=[this_siren], key=f"bouton_{this_siren}", type="tertiary")
        c_siren.text(this_siren)
    st.caption(
        f"Demande actuelle : {len(st.session_state['SIRENS'])} SIREN "
        f"dans {len(st.session_state['departements'])} départements",
        text_alignment='right'
    )

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
    st.caption(
        f"Demande actuelle : {len(st.session_state['SIRENS'])} SIREN "
        f"dans {len(st.session_state['departements'])} départements",
        text_alignment='right'
    )

with tab_resultats:
    disabled = False
    if not st.session_state['SIRENS']:
        st.warning("Il n'y a pas de numéros SIREN")
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
    if not disabled:
        st.markdown(f"Recherche de la propriété des numéros SIRENS **{'**, **'.join(st.session_state['SIRENS'])}** "
                    f"dans les départements : **{'**, **'.join(st.session_state['departements'])}**")
    if bouton_interroger:
        interroge_base()

