from pandas import json_normalize
import pandas as pd
import requests

API_CHARA = "https://genshin.jmp.blue/characters/all?lang=en"
API_ARTI = "https://genshin.jmp.blue/artifacts/all?lang=en"
API_WEAPON = "https://genshin.jmp.blue/weapons/all?lang=en"
JSON_ASCENSION = "ascension_data.json"

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.width = None
pd.options.display.max_colwidth = None

res_CHARA = requests.get(API_CHARA)
res_ARTI = requests.get(API_ARTI)
res_WEAPON = requests.get(API_WEAPON)

data_CHARA = res_CHARA.json()
data_ARTI = res_ARTI.json()
data_WEAPON = res_WEAPON.json()
data_ASCENSION = pd.read_json(JSON_ASCENSION)

df_CHARA = json_normalize(data_CHARA, sep="_")
df_ARTI = json_normalize(data_ARTI, sep="_")
df_WEAPON = json_normalize(data_WEAPON, sep="_")
df_ASCENSION = data_ASCENSION.explode('ascension_data').reset_index(drop=True)
df_ASCENSION = pd.concat([df_ASCENSION.drop(columns=['ascension_data']), pd.json_normalize(df_ASCENSION['ascension_data'])], axis=1)

df_CHARA = df_CHARA.drop(df_CHARA.columns[[1,4,5,6,8,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25,26]], axis=1)
df_ARTI = df_ARTI.drop(df_ARTI.columns[[1,4]],axis=1)
df_WEAPON = df_WEAPON.drop(df_WEAPON.columns[[5,7,8,9]], axis=1)
df_ASCENSION = df_ASCENSION.drop(df_ASCENSION.columns[[1,2,3,4,5]], axis=1)
df_ASCENSION = df_ASCENSION.set_index('name').map(lambda x: pd.notna(x) and str(x).strip() not in ['','0%']).reset_index()
df_ASCENSION = df_ASCENSION.groupby('name').any().reset_index()

df_CHARA = pd.merge(df_CHARA, df_ASCENSION, on='name', how='left')
ascension_col = df_ASCENSION.columns.difference(['name'])
df_CHARA[ascension_col] = df_CHARA[ascension_col].fillna(False)

df_CHARA.to_csv(path_or_buf="CSV_Data/GenshinCharatersClean.csv",index=False)
df_ARTI.to_csv(path_or_buf="CSV_Data/GenshinArtifactsClean.csv",index=False)
df_WEAPON.to_csv(path_or_buf="CSV_Data/GenshinWeaponsClean.csv",index=False)