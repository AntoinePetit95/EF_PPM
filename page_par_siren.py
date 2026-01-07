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
                     "car certains numéros SIREN de la base correspondent à "
                     "une numérotation interne des services de l'état.")
st.title("🪪 Recherche par numéro SIREN", help=info_recherche_pm)

def format_function(dept_code: str) -> str:
    return f"{dept_code} - {DEPARTEMENTS[dept_code]}"

st.multiselect(
    "Départements de recherche",
    DEPARTEMENTS_CODES,
    format_func=format_function,
    key='departements',
    placeholder='Limiter la recherche aux départements ...'
)
if len(st.session_state['departements']) >= 3:
    st.warning(f"Beaucoup de départements ont été sélectionnés, cela peut ralentir la recherche.")

def interroge_base() -> None:
    if not st.session_state['SIRENS']:
        return
    if not st.session_state['departements']:
        return
    with st.spinner("Récupération des informations ...", show_time=True):
        ppm = PPM()
        ppm.fetch_sirens(st.session_state['SIRENS'], limit_to_department=st.session_state['departements'])
        st.session_state['ppm_siren'] = ppm

    if ppm.empty:
        st.info('Aucun résultat !', icon='🫥')
    else:
        st.success("Informations récupérées !", icon="🎉")
        affiche_tableau(st.session_state['ppm_siren'])


def resultats(_id: str) -> None:
    st.divider()
    disabled = False
    if not st.session_state['SIRENS']:
        disabled = True

    if not st.session_state['departements']:
        disabled = True

    cr1, cr2 = st.columns([5,2], vertical_alignment="center")


    query_caption = (f"Demande actuelle : {len(st.session_state['SIRENS'])} SIREN "
                    f"dans {len(st.session_state['departements'])} départements")

    cr1.caption(query_caption, text_alignment='left')
    bouton_interroger = cr2.button(
        icon='🔍',
        label=f"interroger la base",
        disabled=disabled,
        type='primary',
        key=f"query_button_{_id}",
        width='stretch'
    )
    if bouton_interroger:
        interroge_base()

def supprimer_siren(_siren: str) -> None:
    if _siren in st.session_state['SIRENS']:
        st.session_state['SIRENS'].remove(_siren)


tab_pm, tab_fichier, tab_liste_pm = st.container(border=True).tabs([
    'Ajouter une personne morale',
    'Importer un fichier',
    f'Numéros SIREN de la demande'
    ])


with tab_pm:
    siren_input = st.text_input("Numéro SIREN", "519587851")

    siren_est_correct = True

    siren = str(siren_input)

    if not len(siren) >= 9:
        st.warning('le numéro SIREN doit être au moins sur 9 caractères')
        siren_est_correct = False

    bouton_ajouter_siren = st.button(
        icon="➕",
        label='Ajouter',
        width='stretch',
        disabled=not siren_est_correct,
        type='secondary'
    )

    if bouton_ajouter_siren:
        siren = siren.replace(" ", "")
        if siren not in st.session_state['SIRENS']:
            st.session_state['SIRENS'].append(siren)
            st.session_state['parcelles'].sort()
        st.rerun()
    resultats("SIREN")

with tab_fichier:
    fichier = st.file_uploader("Importer des numéro SIREN depuis un fichier excel", type=['xlsx', 'xls'])

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
            col = st.selectbox("Quelle colonne contient les numéros SIREN ?", onglet_df.columns)

        liste_siren = onglet_df[col].dropna().to_list()
        liste_siren = [siren for siren in liste_siren if siren]  # remove None
        liste_siren = [siren for siren in liste_siren if len(siren) >= 9]

        with st.expander("aperçu des numéros SIREN"):
            st.write(pd.DataFrame(liste_siren))

        if not liste_siren:
            caption = "Aucun numéro SIREN"
        else:
            caption = f"Ajouter la liste"

        bouton_ajouter_sirens_depuis_fichier = st.button(
            type='secondary',
            icon="➕",
            width='stretch',
            label=caption,
            disabled=not liste_siren,
        )

        if bouton_ajouter_sirens_depuis_fichier:

            st.session_state['SIRENS'].extend(liste_siren)
            st.session_state['SIRENS'] = list(set(st.session_state['SIRENS']))
            st.session_state['SIRENS'].sort()

    resultats("fichier")

with tab_liste_pm:
    bouton_vider_liste = st.button(
        icon='❌',
        label="Supprimer tout",
        disabled=not st.session_state['SIRENS'],
        type='secondary',
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

