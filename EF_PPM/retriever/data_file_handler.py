import os
from typing import Literal

import pandas as pd

from EF_PPM.utils.group_code import group_code
from EF_PPM.utils.droits_code import codes_droit
from EF_PPM.utils.forme_juridique_code import formes_juridiques
from EF_PPM.utils.column_names_raw_files import RawField
from EF_PPM.utils.field_names import Field


class PPMDataFileHandler:
    filepath: str
    df: pd.DataFrame

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        assert os.path.isfile(self.filepath)
        assert os.path.splitext(self.filepath)[1] in ['.txt', '.csv']

        self.df = pd.read_csv(self.filepath, sep=';', encoding='utf-8', dtype=object)

        # build department and insee fields, for research purposes
        self.df[RawField.DEPARTEMENT.value] = self.df[RawField.DEPARTEMENT.value].str.zfill(2)
        # take only the first 2 chars of department field to construct INSEE (useful for 97X depts)
        self.df["INSEE"] = (
                self.df[RawField.DEPARTEMENT.value].apply(lambda x : x[:2]) +
                self.df[RawField.CODE_COMMUNE.value].str.zfill(3)
        )

        def remove_spaces(s: str | None) -> str:
            if pd.isna(s):
                return ''
            return s.replace(' ', '')

        # build idu
        self.df[Field.IDU.value] = (
                self.df["INSEE"] +
                self.df[RawField.COM_ABS.value].apply(remove_spaces).str.zfill(3) +
                self.df[RawField.SECTION.value].apply(remove_spaces).str.zfill(2) +
                self.df[RawField.NUMERO.value].apply(remove_spaces).str.zfill(4)
        )

        def remove_multiple_spaces(s: str) -> str:
            return " ".join(s.split())

        def to_str_with_spacing(s: str | None) -> str:
            if pd.isna(s):
                return ''
            return f"{s} "

        def to_str(s: str | None) -> str:
            if pd.isna(s):
                return ''
            return f"{s}"

        self.df[RawField.ADRESSE_NUM.value] = self.df[RawField.ADRESSE_NUM.value].apply(to_str_with_spacing)
        self.df[RawField.ADRESSE_REP.value] = self.df[RawField.ADRESSE_REP.value].apply(to_str_with_spacing)
        self.df[RawField.ADRESSE_TYPE_VOIE.value] = self.df[RawField.ADRESSE_TYPE_VOIE.value].apply(to_str_with_spacing)
        self.df[RawField.ADRESSE_NUM.value] = self.df[RawField.ADRESSE_NUM.value].apply(to_str)

        self.df[Field.ADRESSE.value] = self.df[[
            RawField.ADRESSE_NUM.value,
            RawField.ADRESSE_REP.value,
            RawField.ADRESSE_TYPE_VOIE.value,
            RawField.ADRESSE_NOM_VOIE.value
        ]].agg(''.join, axis=1).apply(remove_multiple_spaces)

        self.df[Field.CLASSEMENT_PPT.value] = self.df[RawField.GROUPE_CODE.value].apply(lambda x: group_code.get(x))

        rename_mapping = {
            RawField.COMMUNE.value: Field.COMMUNE.value,
            RawField.SUF.value: Field.SUF.value,
            RawField.NAT_CAD.value: Field.NAT_CAD.value,
            RawField.CONTENANCE.value: Field.CONTENANCE.value,
            RawField.CODE_DROIT.value: Field.CODE_DROIT.value,
            RawField.MAJIC.value: Field.MAJIC.value,
            RawField.SIREN.value: Field.SIREN.value,
            RawField.FORME_JUR_ABR.value: Field.FORME_JURIDIQUE_ABR.value,
            RawField.DENOMINATION.value: Field.DENOMINATION.value,
            RawField.CONTENANCE_SUF.value: Field.CONTENANCE_SUF.value,
        }
        self.df = self.df.rename(columns=rename_mapping)

        def get_first_char(s: str | None) -> str:
            if pd.isna(s):
                return s
            return s[0]

        self.df[Field.CODE_DROIT.value] = self.df[Field.CODE_DROIT.value].apply(get_first_char)
        self.df[Field.LBL_DROIT.value] = self.df[Field.CODE_DROIT.value].apply(lambda x: codes_droit.get(x))
        self.df[Field.FORME_JURIDIQUE.value] = self.df[RawField.FORME_JURIDIQUE_CODE.value].apply(lambda x: formes_juridiques.get(x))
        self.df[Field.CONTENANCE.value] = self.df[Field.CONTENANCE.value].astype(int)

    @property
    def clean_table(self) -> pd.DataFrame:
        fields_to_keep = [f.value for f in Field]
        return self.df[fields_to_keep]


    def filter_by_references(self, references: list[str]) -> pd.DataFrame:
        return_df = pd.DataFrame(columns=[f.value for f in Field])

        plot_references = [r for r in references if len(r) == 14]
        if len(plot_references) != 0:
            df_search = self.clean_table[self.df[Field.IDU.value].isin(plot_references)]
            return_df = pd.concat([return_df, df_search])

        municipality_references = [r for r in references if len(r) == 5]
        if len(municipality_references) != 0:
            df_search = self.clean_table[self.df["INSEE"].isin(municipality_references)]
            return_df = pd.concat([return_df, df_search])

        # overkill, because the entire file is supposed to be on the same department
        dept_references = [r for r in references if len(r) <= 3]
        if len(dept_references) != 0:
            df_search = self.clean_table[self.df[RawField.DEPARTEMENT.value].isin(dept_references)]
            return_df = pd.concat([return_df, df_search])

        return return_df

    def filter_by_siren(self, sirens: list[str]) -> pd.DataFrame:
        return_df = pd.DataFrame(columns=[f.value for f in Field])

        if len(sirens) != 0:
            df_search = self.clean_table[self.df[Field.SIREN.value].isin(sirens)]
            return_df = pd.concat([return_df, df_search])

        return return_df

    def filter_by_name(self, name: str, mode: Literal['exact', 'contains']) -> pd.DataFrame:
        return_df = pd.DataFrame(columns=[f.value for f in Field])

        if len(name) != 0:
            if mode == 'exact':
                df_search = self.clean_table[self.df[Field.DENOMINATION.value]==name]
            elif mode == 'contains':
                df_search = self.clean_table[self.df[Field.DENOMINATION.value].str.contains(name)]
            else:
                raise ValueError(mode)
            return_df = pd.concat([return_df, df_search])

        return return_df
