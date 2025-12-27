from EF_PPM import PPM, get_plots_from_excel_file

folder_path = r''
excel_file = rf'{folder_path}'
tab_name = 'Feuil1'
column = 'idu'
plots = get_plots_from_excel_file(file_path=excel_file, tab_name=tab_name, column_name=column)

ppm = PPM()
ppm.fetch_cad_refs(plots)
ppm.merged_suf.save_to_excel(folder_path=folder_path)

