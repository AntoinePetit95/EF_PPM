import streamlit as st
import pandas as pd

from EF_PPM.retriever.retriever import PPM


@st.fragment
def affiche_tableau(ppm:PPM) -> None:

    ppm_to_show = ppm

    help_suf = ("La **subdivision fiscale (suf)** est une partie de parcelle ayant la même nature de culture "
                "(c’est-à-dire la même affectation fiscale). Il est très rare que les SUF d'une même parcelle "
                "aient des propriétaires différents, il est conseillé de les regrouper pour une lecture plus simple.")
    group_by_suf = st.toggle("Grouper les SUF (recommandé)", help=help_suf, value=True)
    if group_by_suf:
        ppm_to_show = ppm_to_show.merged_suf

    help_pm = "Grouper les personnes morales sur une seule ligne."
    group_by_pm = st.toggle("Grouper les PM", help=help_pm, value=False)
    if group_by_pm:
        ppm_to_show = ppm_to_show.merged_rights

    help_essential = "Ne conserver que les informations essentielles."
    show_only_essential = st.toggle("Simplifier (recommandé)", help=help_essential, value=True)
    if show_only_essential:
        ppm_to_show = ppm_to_show.essential

    ppm_to_show.sort_by_idu()

    styler = ppm_to_show.na_as_empty_string().table.style.hide().bar(
        subset=['contenance'], align="mid", color="#82C46C"
    ).set_table_styles([
          {"selector": "th", "props": [("font-size", "11px")]},           # en-têtes
          {"selector": "td", "props": [("font-size", "11px")]},           # cellules
      ])

    with st.container(height=300):
        st.write(styler.to_html(), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c2.caption(f"{len(ppm_to_show.table)} lignes", text_alignment='right')
    downloaded = c1.download_button(
        "Télécharger la table",
        data=ppm_to_show.excel_file_bytes,
        mime="application/octet-stream",
        file_name="Énergie_Foncière_parcellaire_PM.xlsx",
    )

    if downloaded:
        st.success("**Et voilà !**   \n   \n**Énergie Foncière** met cet outil à disposition pour simplifier l’accès à "
                   "la donnée foncière.   \nCela vous a été utile ? Laissez-nous un "
                   "👍 [**avis Google**](https://g.page/r/CXS-zJLN66DrEAE/review) ou "
                   "💬 [**discutons ensemble**](https://www.linkedin.com/in/antoine-petit-ef/) !")


help_idu = ("L'identifiant unique (IDU) est la référence à une parcelle, en 14 caractères. Il est composé :  \n"
            "du **code Insee** de la commune (5 caractères),  \n"
            "du **code de commune absorbée** (3 caractères, souvent 000),  \n"
            "de la **section** sur 2 caractères (A devient 0A),  \n"
            "et du **numéro cadastral** sur 4 caractères (1 devient 0001).")


def initialize_values() -> None:
    values = {
        'parcelles': [],
        'ppm_parcelles': PPM(),
    }
    for k, v in values.items():
        if k not in st.session_state.keys():
            st.session_state[k] = v

initialize_values()

st.title("1️⃣ Recherche par parcelles")


def interroge_base() -> None:
    if not st.session_state['parcelles']:
        return

    with st.spinner("Récupération des informations ...", show_time=True):
        ppm = PPM()
        ppm.fetch_cad_refs(st.session_state['parcelles'])
        st.session_state['ppm_parcelles'] = ppm

    if ppm.empty:
        st.info('Aucun résultat !', icon='🫥')
    else:
        st.success("Informations récupérées !", icon="🎉")
        affiche_tableau(st.session_state['ppm_parcelles'])

def resultats(_id: str) -> None:
    st.divider()
    cr1, cr2 = st.columns([5,2], vertical_alignment="center")

    if len(st.session_state['parcelles']) == 0:
        query_caption = f"Aucunes parcelles à demander"
    else:
        query_caption = f"**{len(st.session_state['parcelles'])}** parcelles dans la demande"

    cr1.caption(query_caption, text_alignment='left')
    bouton_interroger = cr2.button(
        icon='🔍',
        label=f"interroger la base",
        disabled=not st.session_state['parcelles'],
        type='primary',
        key=f"query_button_{_id}",
        width='stretch'
    )
    if bouton_interroger:
        interroge_base()

def supprimer_parcelle(id_parcelle: str) -> None:
    if id_parcelle in st.session_state['parcelles']:
        st.session_state['parcelles'].remove(id_parcelle)


tab_parcelle, tab_fichier, tab_liste_parcelles = st.tabs([
    'Ajouter une parcelle', 'Importer un fichier', f'Parcelles de la demande'
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
        icon="➕",
        label='Ajouter',
        disabled=not id_parcelle_est_correct,
        type='secondary',
        width='stretch'
    )

    if bouton_ajouter_parcelle:
        if id_parcelle not in st.session_state['parcelles']:
            st.session_state['parcelles'].append(id_parcelle)
            st.session_state['parcelles'].sort()
        st.rerun()

    resultats("parcelles")

with tab_fichier:
    fichier = st.file_uploader("Importer des parcelles depuis un fichier excel", type=['xlsx', 'xls'])

    if fichier:
        excel_file = pd.ExcelFile(fichier)
        if len(excel_file.sheet_names) > 1:
            onglet = st.selectbox("plusieurs onglets existent. Lequel choisir ?", excel_file.sheet_names)
        else:
            onglet=0
        onglet_df = pd.read_excel(fichier, sheet_name=onglet, dtype='str')

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
            caption = "Pas de parcelles à ajouter"
        else:
            caption = f"Ajouter la liste"

        bouton_ajouter_parcelle_depuis_fichier = st.button(
            type='secondary',
            icon="➕",
            label=caption,
            disabled=not liste_idu,
            width='stretch'
        )

        if bouton_ajouter_parcelle_depuis_fichier:

            st.session_state['parcelles'].extend(liste_idu)
            st.session_state['parcelles'] = list(set(st.session_state['parcelles']))
            st.session_state['parcelles'].sort()

    st.caption(f"{len(st.session_state['parcelles'])} parcelles dans la demande", text_alignment='right')

    resultats("fichier")

with tab_liste_parcelles:
    bouton_vider_liste = st.button(
        icon='❌',
        label="Supprimer tout",
        disabled=not st.session_state['parcelles'],
        type='secondary',
        width='stretch'
    )

    if bouton_vider_liste:
        st.session_state['parcelles'] = []
        st.rerun()

    for id_parcelle in st.session_state['parcelles']:
        c_bout, c_parc = st.columns([1, 20], vertical_alignment='center', gap=None)
        c_bout.button(":x:", on_click=supprimer_parcelle, args=[id_parcelle], key=f"bouton_{id_parcelle}", type="tertiary")
        c_parc.text(id_parcelle)
    st.caption(f"{len(st.session_state['parcelles'])} parcelles dans la demande", text_alignment='right')

    resultats("liste")

