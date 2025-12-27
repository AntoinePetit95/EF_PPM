
# Parcellaire PM
Parcellaire PM est à la fois un **module python** et une **application streamlit**, 
tous deux gratuits et libres d'utilisation, permettant d'explorer simplement les données des parcelles des personnes 
morales des services de l'état.

## Que sont les fichiers des parcelles des personnes morales (PPM) ?
Les fichiers des PPM recensent au niveau départemental les personnes morales ayant des droits fonciers 
sur des immeubles, en situation du 1er janvier de l'année de référence, à l'exception des sociétés 
unipersonnelles et des entrepreneurs individuels.  

Les fichiers sont sous Licence Ouverte / Open Licence version 2.0. Ils sont mis à disposition par 
les services de l'état à l'adresse suivante : 
https://www.data.gouv.fr/fr/datasets/fichiers-des-locaux-et-des-parcelles-des-personnes-morales/


Les fichiers des PPM sont composés de deux données : 
- Les fichiers des propriétés bâties (locaux).
- Les fichiers des propriétés non bâties (parcelles). **Seul ce dernier est exploité par Parcellaire PM.**


## Application Streamlit

[Accéder à l'application Streamlit](https://energie-fonciere-parcellaire-pm.streamlit.app/)  

L’application Streamlit, accessible via un navigateur, permet d’interroger rapidement les fichiers PPM 
sans avoir à manipuler les CSV bruts. 
Deux modes de recherche sont disponibles :

- **Recherche par parcelles** : saisissez une ou plusieurs références cadastrales (format parcelle), 
ajoutez-les à la liste, puis lancez la recherche.

- **Recherche par SIREN** : saisissez un ou plusieurs numéros SIREN, en limitant la recherche à un ou 
plusieurs départements. Cette restriction est fortement recommandée pour éviter de parcourir 
l’intégralité de la base, ce qui peut être long.

Dans les deux cas, vous pouvez constituer une liste de références (parcelles ou SIREN) avant 
d’exécuter la requête. Une fois les résultats affichés, vous pouvez télécharger les fichiers 
au format “simplifié” (données regroupées et plus lisibles) ou au format “entier” 
(données détaillées telles que présentes dans la source).


## Module Python
[Repository Github](https://github.com/AntoinePetit95/EF_PPM/tree/master)  

Le module python vous sera utile si vous souhaitez exploiter directement dans Python ou bien dans Excel la propriété des personnes morales.
Attention : le module fonctionne en gardant une copie locale des fichiers au format CSV (3,5 Go environ), il faut prévoir qu'il est plutôt lourd. 
Ce choix a été fait en l'absence d'API libre de droits en ligne, et permet l'interrogation de la base avec une 
liste de références (parcelles, communes, départements, ou par propriétaire).


Voici un exemple de code pour interagir avec le module :

```python
from EF_PPM import PPM

# initialisation de l'objet PPM
ppm = PPM()

# exemple de demande par références cadastrales
exemple_parcelle = '02001000AC0145'
exemple_commune = '78048'
exemple_departement = '85'  # possible mais traitement long
references = [exemple_parcelle, exemple_commune]
ppm.fetch_cad_refs(references)

# exemple de demande par numéro siren
sirens = ["519587851"]
ppm.fetch_sirens(sirens=sirens, limit_to_department=['75'])

# table des PPM en entier, sous la forme d'un tableau pandas DataFrame
print(ppm.table)

# PPM, compressée en une ligne pour tout les droits sur chaque terrains
print(ppm.merged_rights.table)

# PPM, sans faire la distinction entre les SUF (sous-unités foncières)
print(ppm.merged_suf.table)

# PPM sans SUF et en une seule ligne par parcelle
print(ppm.merged_suf.merged_rights.table)

# export vers excel
ppm.merged_suf.save_to_excel(folder_path='your_folder_path', name='fichier_ppm')
```

## Licence
Ce projet est libre d'utilisation, sous la licence suivante : 
[The Unlicense](https://choosealicense.com/licenses/unlicense/)

## Auteur
Développé par [Antoine PETIT](https://github.com/AntoinePetit95), d'[Energie Foncière](https://energie-fonciere.fr/).
Discutons ensemble sur [LinkedIn](https://www.linkedin.com/in/antoine-petit-28a056141/) !

## Acknowledgements
 - [Fichiers des locaux et des parcelles des personnes morales](https://www.data.gouv.fr/fr/datasets/fichiers-des-locaux-et-des-parcelles-des-personnes-morales/)
 - [Awesome Readme Templates](https://awesomeopensource.com/project/elangosundar/awesome-README-templates)
 - [Awesome README](https://github.com/matiassingers/awesome-readme)
 - [How to write a Good readme](https://bulldogjob.com/news/449-how-to-write-a-good-readme-for-your-github-project)

