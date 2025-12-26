import os

import streamlit as st
from EF_PPM.retriever.retriever import PPM
import pandas as pd

help_idu = ("L'identifiant unique (IDU) est la référence à une parcelle, en 14 caractères. Il est composé :  \n"
            "du **code Insee** de la commune (5 caractères),  \n"
            "du **code de commune absorbée** (3 caractères, souvent 000),  \n"
            "de la **section** sur 2 caractères (A devient 0A),  \n"
            "et du **numéro cadastral** sur 4 caractères (1 devient 0001).")

help_outil = ("**Parcellaire PM** est un outil gratuit conçu par **Énergie Foncière** pour simplifier "
              "l’exploitation des fichiers annuels de parcelles détenues par des personnes morales. "
              "À partir d’une parcelle ou d’une liste de références cadastrales, il permet d’identifier "
              "les propriétaires concernés puis d’exporter les résultats.")


with st.sidebar:
    logo_path = f".{os.sep}EF_PPM{os.sep}assets{os.sep}LOGO-EF-RVB.svg"
    st.logo(logo_path, size='large', link='https://energie-fonciere.fr/')
    st.title("Parcellaire PM", help=help_outil)
    st.caption("Le foncier des personnes morales, simplement !")


def initialize_values() -> None:
    values = {
        'parcelles': [],
        'df': pd.DataFrame(),
    }
    for k, v in values.items():
        if k not in st.session_state.keys():
            st.session_state[k] = v

initialize_values()

def interroge_base() -> None:
    if not st.session_state['parcelles']:
        return
    with st.status("Récupération des informations ...", expanded=True) as status:
        ppm = PPM()
        ppm.fetch(st.session_state['parcelles'])
        st.session_state['ppm_parcelles'] = ppm
        status.update(
            label="Informations récupérées !", state="complete", expanded=True
        )
        st.write(st.session_state['ppm_parcelles'].merged_suf.essential.table)
        c1, c2 = st.columns(2)
        c1.download_button(
            "télécharger (données simplifiée)",
            data=st.session_state['ppm_parcelles'].merged_suf.essential.excel_file_bytes,
            mime="application/octet-stream",
            file_name="Énergie_Foncière_parcellaire_PM.xlsx"
        )
        c2.download_button(
            "télécharger (données complètes)",
            data=st.session_state['ppm_parcelles'].merged_suf.excel_file_bytes,
            mime="application/octet-stream",
            file_name="Énergie_Foncière_parcellaire_PM.xlsx"
        )


def supprimer_parcelle(id_parcelle: str) -> None:
    if id_parcelle in st.session_state['parcelles']:
        st.session_state['parcelles'].remove(id_parcelle)


st.title("Recherche par parcelles")
tab_parcelle, tab_fichier, tab_liste_parcelles, tab_resultats = st.tabs([
    'Ajouter une parcelle', 'Importer un fichier', f'Parcelles [{len(st.session_state['parcelles'])}]', 'Résultats'
])


with tab_parcelle:
    columns_id_parcelle = st.columns(4)
    insee_input = columns_id_parcelle[0].text_input("Code Insee de la commune", "75107", max_chars=5)
    com_abs_input = columns_id_parcelle[1].text_input("Code commune absorbée", "000", max_chars=3)
    section_input = columns_id_parcelle[2].text_input("Section", "CR", max_chars=2)
    numero_input = columns_id_parcelle[3].text_input("Numéro cadastral", "1",max_chars=4)

    id_parcelle_est_correct = True

    insee = str(insee_input)
    com_abs = str(com_abs_input).zfill(3)
    section = str(section_input).zfill(2)
    numero = str(numero_input).zfill(4)

    if not all([c.isnumeric() for c in insee]):
        if insee.startswith('2A') or insee.startswith('2B'):
            if not all([c.isnumeric() for c in insee[2:]]):
                st.warning("le code Insee doit être entièrement numérique après 2A ou 2B")
                id_parcelle_est_correct = False
        else:
            st.warning("le code Insee doit être entièrement numérique (à l'exception des départements 2A et 2B)")
            id_parcelle_est_correct = False
    if not all([c.isnumeric() for c in com_abs]):
        st.warning('le code de commune absorbée doit être entièrement numérique')
        id_parcelle_est_correct = False
    if not all([c.isnumeric() for c in numero]):
        st.warning('le numéro cadastral doit être entièrement numérique')
        id_parcelle_est_correct = False

    if not len(insee) == 5:
        st.warning('le code insee doit être sur 5 caractères')
        id_parcelle_est_correct = False
    if not len(com_abs) == 3:
        st.warning('le code de commune absorbée doit être sur 3 caractères')
        id_parcelle_est_correct = False
    if not len(section) == 2:
        st.warning('la section doit être sur 2 caractères')
        id_parcelle_est_correct = False
    if not len(numero) == 4:
        st.warning('le numéro cadastral doit être sur 4 caractères')
        id_parcelle_est_correct = False


    id_parcelle = f"{insee}{com_abs}{section}{numero}"

    if not id_parcelle_est_correct:
        caption = "IDU non valide"
    else:
        caption = f"IDU : {id_parcelle}"

    st.caption(caption, text_alignment='right', help=help_idu)
    bouton_ajouter_parcelle = st.button(
        label='ajouter à la demande',
        disabled=not id_parcelle_est_correct,
        type='primary'
    )

    if bouton_ajouter_parcelle:
        if id_parcelle not in st.session_state['parcelles']:
            st.session_state['parcelles'].append(id_parcelle)
            st.session_state['parcelles'].sort()
        st.rerun()


with tab_fichier:
    fichier = st.file_uploader("Importer des parcelles depuis un fichier excel", type=['xlsx', 'xls'])

    if fichier:
        excel_file = pd.ExcelFile(fichier)
        if len(excel_file.sheet_names) > 1:
            onglet = st.selectbox("plusieurs onglets existent. Lequel choisir ?", excel_file.sheet_names)

        onglet_df = pd.read_excel(fichier, sheet_name=onglet)

        with st.expander("aperçu de l'onglet"):
            st.write(onglet_df)

        if len(onglet_df.columns) > 1:
            col = st.selectbox("Quelle colonne contient les IDU ?", onglet_df.columns, help=help_idu)

        liste_idu = onglet_df[col].dropna().to_list()
        liste_idu = [idu for idu in liste_idu if idu]  # remove None
        liste_idu = [idu for idu in liste_idu if len(idu) == 14]

        with st.expander("aperçu des identifiants uniques parcelles"):
            st.write(pd.DataFrame(liste_idu))

        if not liste_idu:
            caption = "pas de parcelles"
        else:
            caption = f"ajouter les parcelles"

        bouton_ajouter_parcelle_depuis_fichier = st.button(
            label=caption,
            disabled=not liste_idu,
        )

        if bouton_ajouter_parcelle_depuis_fichier:

            st.session_state['parcelles'].extend(liste_idu)
            st.session_state['parcelles'] = list(set(st.session_state['parcelles']))
            st.session_state['parcelles'].sort()
            st.rerun()


with tab_liste_parcelles:
    bouton_vider_liste = st.button(
        label="Vider la liste des parcelles",
        disabled=not st.session_state['parcelles'],
        type='primary',
    )

    if bouton_vider_liste:
        st.session_state['parcelles'] = []
        st.rerun()

    for id_parcelle in st.session_state['parcelles']:
        c_bout, c_parc = st.columns([1, 20], vertical_alignment='center', gap=None)
        c_bout.button(":x:", on_click=supprimer_parcelle, args=[id_parcelle], key=f"bouton_{id_parcelle}", type="tertiary")
        c_parc.text(id_parcelle)


with tab_resultats:
    bouton_interroger = st.button(
        label="interroger la base",
        disabled=not id_parcelle_est_correct,
        type='primary'
    )
    if bouton_interroger:
        interroge_base()
