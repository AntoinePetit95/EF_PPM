import copy
import io
import os.path
from enum import EnumType
import pandas as pd
from pandas.core.indexes.api import union_indexes

from EF_PPM.retriever.data_folder_handler import PPMDataFolderHandler
from EF_PPM.retriever.data_file_handler import PPMDataFileHandler
from EF_PPM.utils.dept_code import get_dept_code_from_reference_code, ALL_DEPARTMENTS
from EF_PPM.utils.field_names import Field, plot_fields, right_fields


class PPM:
    table: pd.DataFrame
    ppm_data_folder: PPMDataFolderHandler

    def __init__(self) -> None:
        self.table = pd.DataFrame(columns=[Field.IDU.value])
        self.ppm_data_folder = PPMDataFolderHandler()

    @property
    def merged_rights(self) -> 'PPM':
        """
        Concatenates rights along IDU and SUF (if exists)
        :return: copy of the PPM object
        """
        new_ppm = copy.deepcopy(self)

        # fields to use ase index temporarily : IDU + SUF (if available)
        id_fields = [Field.IDU.value]
        if Field.SUF.value in new_ppm.table.columns:
            id_fields.append(Field.SUF.value)

        # we want a table with a unique index. Start : create a new table with only the plot info
        plot_columns = [f.value for f in plot_fields()]
        new_ppm.table = new_ppm.table[plot_columns].drop_duplicates(ignore_index=True).set_index(id_fields)

        # aggregate rights and right holders
        original_df = self.table.set_index(id_fields)
        columns_to_aggregate = [f.value for f in right_fields()]
        for column_name in columns_to_aggregate:
            new_ppm.table[column_name] = [
                ', '.join(list(set(original_df.loc[[i], column_name].tolist())))
                for i in new_ppm.table.index
            ]

        # finally : drop index (keep IDU and SUF as column)
        new_ppm.table = new_ppm.table.reset_index()
        return new_ppm

    @property
    def essential(self) -> 'PPM':
        """
        Only essentials values
        :return: copy of the PPM object
        """
        new_ppm = copy.deepcopy(self)

        fields_to_keep_and_order = [
            Field.IDU.value,
            Field.ADRESSE.value,
            Field.CONTENANCE,
            Field.LBL_DROIT.value,
            Field.DENOMINATION.value,
            Field.SIREN.value,
        ]

        fields_to_keep_and_order = [f for f in fields_to_keep_and_order if f in new_ppm.table.columns]
        new_ppm.table = new_ppm.table[fields_to_keep_and_order]

        return new_ppm

    @property
    def merged_suf(self) -> 'PPM':
        """
        Merges SUF and drop duplicates for the same IDU (plot id). Duplicates are : same right, same right holder, and same plot.
        Will aggregate plot information dependent on SUF : SUF, NAT_CAD, CONTENANCE_SUF
        :return: copy of the PPM object
        """
        # create a new PPM object
        new_ppm = copy.deepcopy(self)

        # drop duplicates. Duplicates are same plot id, same person, and same right.
        fields_defining_duplicates = [Field.IDU.value, Field.CODE_DROIT.value, Field.MAJIC.value]
        new_ppm.table = new_ppm.table.drop_duplicates(subset=fields_defining_duplicates)

        # temporary : use IDU as index
        new_ppm.table = new_ppm.table.set_index(Field.IDU.value)
        original_df = self.table.set_index(Field.IDU.value)

        # aggregate SUF dependent info
        suf_dependent_info = [Field.SUF.value, Field.CONTENANCE_SUF.value, Field.NAT_CAD.value]
        for column in suf_dependent_info:
            new_ppm.table[column] = [
                ', '.join([
                    str(v) or '' for v in set(original_df.loc[[i], column])
                ])
                for i in new_ppm.table.index
            ]
        # finally : drop index (keep IDU)
        new_ppm.table = new_ppm.table.reset_index()

        return new_ppm

    def fetch_all(self, limit_to_department: list[str] | None = None) -> None:
        if limit_to_department:
            department_to_search = limit_to_department
        else:
            department_to_search = ALL_DEPARTMENTS

        for dept in department_to_search:
            files = self.ppm_data_folder.departmental_files(dept)
            for f in files:
                ppm_file = PPMDataFileHandler(f)
                df = ppm_file.df
                self.table = pd.concat([self.table, df], ignore_index=True)

        self.table.drop_duplicates(inplace=True, ignore_index=True)

    def fetch(self, references: str | list[str], limit_to_department: list[str] | None = None) -> None:
        """
        Fetch all PM plots for this set of references and add it to parent.
        :param limit_to_department: départements to concentrate the search into
        :param references: Reference(s) for plots (IDU: 14 chars) or municipalities (5 chars) or dept (2-3 chars)
        :return: None
        """

        if type(references) is str:
            references = [references]

        assert all([len(ref) in [14, 5, 3, 2] for ref in references])
        dept_codes = get_dept_code_from_reference_code(references)
        unique_depts = list(set(dept_codes))

        references_by_dept = {
            dept: [reference for ref_dept, reference in zip(dept_codes, references) if ref_dept == dept]
            for dept in unique_depts
        }

        if limit_to_department:
            department_to_search = limit_to_department
        else:
            department_to_search = ALL_DEPARTMENTS

        depts = [dept for dept in unique_depts if dept in department_to_search]

        for dept in depts:
            files = self.ppm_data_folder.departmental_files(dept)
            for f in files:
                ppm_file = PPMDataFileHandler(f)
                df = ppm_file.filter_by_references(references_by_dept[dept])
                self.table = pd.concat([self.table, df], ignore_index=True)

        self.table.drop_duplicates(inplace=True, ignore_index=True)

    def get_from_owner(
            self,
            sirens: list[str] | None = None,
            limit_to_department: list[str] | None = None) -> None:
        if limit_to_department:
            department_to_search = limit_to_department
        else:
            department_to_search = ALL_DEPARTMENTS

        for dept in department_to_search:
            files = self.ppm_data_folder.departmental_files(dept)
            for f in files:
                ppm_file = PPMDataFileHandler(f)
                df = ppm_file.filter_by_siren(sirens)
                self.table = pd.concat([self.table, df], ignore_index=True)

    def save_to_excel(self, folder_path: str, name: str | None = None) -> None:
        if not name:
            name = 'parcelles_personnes_morales'
        assert os.path.isdir(folder_path)
        file_path = fr'{folder_path}{os.path.sep}{name}.xlsx'
        self.table.to_excel(file_path, index=False)

    @property
    def excel_file_bytes(self) -> io.BytesIO:
        excel_file_buffer = io.BytesIO()
        self.table.to_excel(excel_file_buffer, index=False)
        excel_file_buffer.seek(0)
        return excel_file_buffer

    @staticmethod
    def field_names() -> list[str]:
        return [f.value for f in Field]

    @staticmethod
    def field_enum() -> EnumType:
        return Field
