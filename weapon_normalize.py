import pandas as pd
import re
from collections import defaultdict

df = pd.read_csv('CSV_Data/GenshinWeaponsClean.csv')

feature_config = {
    'ATK_percent': r'ATK\s*(?:increased by|by|boosted by|↑)\s*(\d+\.?\d*)%',
    'CRIT_Rate_percent': r'CRIT Rate\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'CRIT_DMG_percent': r'CRIT DMG\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'HP_percent': r'HP\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'DEF_percent': r'DEF\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'Energy_Recharge_percent': r'Energy Recharge\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'Elemental_Mastery_flat': r'Elemental Mastery\s*(?:increased by|by|↑)\s*(\d+)',
    'Normal_Attack_DMG_percent': r'Normal Attack DMG\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'Charged_Attack_DMG_percent': r'Charged Attack DMG\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'Elemental_Skill_DMG_percent': r'Elemental Skill DMG\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'Elemental_Burst_DMG_percent': r'Elemental Burst DMG\s*(?:increased by|by|↑)\s*(\d+\.?\d*)%',
    'Elemental_DMG_Bonus': r'(\d+\.?\d*)%\s*(?:All )?Elemental DMG Bonus',
    'Condition_HP_below_50': r'HP (?:≤|<=?|is below) 50%',
    'Trigger_Off_Field': r'even when (?:off-field|not on field)',
    'Max_Stacks': r'(?:max|up to) (\d+) stacks?',
    'Stack_Duration': r'(\d+)s(?:ec)?\s*duration'
}

def parse_passive(text):
    features = defaultdict(float)
    if pd.isna(text) or text == '-':
        return features
    
    for pattern_name, pattern in feature_config.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if '%' in pattern and match.group(1):
                value = float(match.group(1)) / 100
                features[pattern_name] += value
            elif pattern_name == 'Elemental_Mastery_flat' and match.group(1):
                features[pattern_name] += int(match.group(1))
            elif pattern_name == 'Max_Stacks' and match.group(1):
                features[pattern_name] = int(match.group(1))
            elif pattern_name == 'Stack_Duration' and match.group(1):
                features[pattern_name] = float(match.group(1))
    
    elemental_matches = re.findall(r'(\d+\.?\d*)% (Pyro|Hydro|Cryo|Electro|Anemo|Geo|Dendro) DMG', text)
    for value, element in elemental_matches:
        features[f'{element}_DMG_Bonus'] = float(value) / 100
    
    features['Condition_HP_below_50'] = 1.0 if re.search(feature_config['Condition_HP_below_50'], text) else 0.0
    features['Trigger_Off_Field'] = 1.0 if re.search(feature_config['Trigger_Off_Field'], text) else 0.0
    
    return features

def process_weapon(row):
    features = parse_passive(row['passiveDesc'])
    return pd.Series(features)

features_df = df.apply(process_weapon, axis=1)

df = pd.concat([df, features_df], axis=1)

percentage_cols = [
    col for col in features_df.columns 
    if 'percent' in col or 'Bonus' in col
]

df[percentage_cols] = df[percentage_cols].fillna(0)
df[percentage_cols] = df[percentage_cols].clip(upper=1.0)

df = df.drop_duplicates(subset=['name'], keep='first')
df.to_csv('CSV_Data/GenshinWeaponsProcessed.csv', index=False)
print("Processing successful! File saved.")