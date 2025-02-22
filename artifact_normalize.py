import pandas as pd
import re
from collections import defaultdict

# Load the artifact data
df = pd.read_csv('CSV_Data/GenshinArtifactsClean.csv')

# =====================================================================
# 1. Simplified Regex Patterns with Consistent Group Indexing
# =====================================================================
# Unified regex pattern for percentage-based stats: "% Value followed by Stat Name"
percentage_pattern = r'(\d+\.?\d*)%\s*(ATK|CRIT Rate|HP|DEF|Energy Recharge|Healing Bonus|Shield Strength|Pyro|Hydro|Cryo|Electro|Anemo|Geo|Dendro|Physical)(?:\s*DMG|\s*Damage| Bonus)?'

# Regex for flat values like Elemental Mastery
flat_pattern = r'(\d+)\s*(Elemental Mastery|EM)'

# Reaction bonuses
reaction_pattern = r'(\d+\.?\d*)%\s*(Overloaded|Electro-Charged|Superconduct|Swirl|Vaporize|Melt|Bloom|Hyperbloom|Burgeon)\s*(DMG|Damage)'

# Initialize all feature columns
features = [
    # Core stats
    'ATK_percent', 'CRIT_Rate_percent', 'HP_percent', 'DEF_percent',
    'Energy_Recharge_percent', 'Elemental_Mastery', 'Healing_Bonus_percent',
    'Shield_Strength_percent',
    
    # Elemental/Physical DMG
    *[f'{elem}_DMG_Bonus' for elem in ['Pyro','Hydro','Cryo','Electro','Anemo','Geo','Dendro','Physical']],
    
    # Reaction bonuses
    *[f'{react}_Bonus' for react in ['Overloaded','Electrocharged','Superconduct','Swirl','Vaporize','Melt','Bloom','Hyperbloom','Burgeon']],
    
    # Conditions
    'Condition_HP_below_50', 'Condition_HP_below_70',
    'Trigger_After_Skill', 'Trigger_After_Burst',
    
    # Durations & stacks
    'Duration_seconds', 'Max_Stacks',
    
    # Special mechanics
    'Convert_Healing_To_DMG'
]


# =====================================================================
# 2. Robust Text Processing
# =====================================================================
def process_bonus(text):
    features = defaultdict(float)
    
    if pd.isna(text):
        return features
    
    # 1. Percentage-based stats (ATK%, CRIT Rate%, Elemental DMG, etc.)
    for match in re.finditer(percentage_pattern, text, re.IGNORECASE):
        value = float(match.group(1)) / 100
        stat = match.group(2).strip().lower()
        
        # Map to feature columns
        if stat == 'atk':
            features['ATK_percent'] += value
        elif stat == 'crit rate':
            features['CRIT_Rate_percent'] += value
        elif stat == 'hp':
            features['HP_percent'] += value
        elif stat == 'def':
            features['DEF_percent'] += value
        elif stat == 'energy recharge':
            features['Energy_Recharge_percent'] += value
        elif stat == 'healing bonus':
            features['Healing_Bonus_percent'] += value
        elif stat == 'shield strength':
            features['Shield_Strength_percent'] += value
        elif stat in ['pyro','hydro','cryo','electro','anemo','geo','dendro']:
            features[f'{stat.capitalize()}_DMG_Bonus'] += value
        elif stat == 'physical':
            features['Physical_DMG_Bonus'] += value
    
    # 2. Flat values (Elemental Mastery)
    for match in re.finditer(flat_pattern, text, re.IGNORECASE):
        features['Elemental_Mastery'] += float(match.group(1))
    
    # 3. Reaction bonuses
    for match in re.finditer(reaction_pattern, text, re.IGNORECASE):
        value = float(match.group(1)) / 100
        react = match.group(2).replace('-', '').capitalize()
        features[f'{react}_Bonus'] += value
    
    # 4. Conditions
    if re.search(r'HP (?:≤|<=?|is below) 50%', text):
        features['Condition_HP_below_50'] = 1.0
    if re.search(r'HP (?:≤|<=?|is below) 70%', text):
        features['Condition_HP_below_70'] = 1.0
    
    # 5. Durations
    duration = re.search(r'(\d+)s', text)
    if duration:
        features['Duration_seconds'] = float(duration.group(1))
    
    return features

# =====================================================================
# 3. Process All Rows
# =====================================================================
def process_artifact(row):
    combined_features = defaultdict(float)
    
    for bonus_col in ['2-piece_bonus', '4-piece_bonus']:
        if pd.notna(row[bonus_col]):
            bonus_features = process_bonus(row[bonus_col])
            for key, val in bonus_features.items():
                combined_features[key] += val
    
    # Special cases
    if 'Ocean-Hued Clam' in row['name']:
        combined_features['Convert_Healing_To_DMG'] = 1.0
    
    return pd.Series(combined_features)

features_df = df.apply(process_artifact, axis=1)

# Now join with original data using suffixes
df = df.join(features_df, rsuffix='_artifact')

# =====================================================================
# 4. Clean Up Columns (Remove duplicate columns if needed)
# =====================================================================
# Drop original bonus columns if desired
df = df.drop(columns=['2-piece_bonus', '4-piece_bonus'])

# Final percentage capping
percentage_cols = [col for col in features_df.columns if 'percent' in col or 'Bonus' in col]
df[percentage_cols] = df[percentage_cols].clip(upper=1.0)

df.to_csv('CSV_Data/GenshinArtifactProcessed.csv', index=False)
print("Processed data saved to CSV_Data/GenshinArtifactProcessed.csv")