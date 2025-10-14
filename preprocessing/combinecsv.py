import pandas as pd
import glob

rename_map = {
    "Country": "Country or region",
    "Happiness.Rank": "Overall rank",
    "Happiness Rank" : "Overall rank",
    "Happiness.Score": "Score",
    "Happiness Score" : "Score",
    "Economy..GDP.per.Capita.": "GDP per capita",
    "Economy (GDP per Capita)" : "GDP per capita",
    "Family": "Social support",
    "Health..Life.Expectancy.": "Healthy life expectancy",
    "Health (Life Expectancy)": "Healthy life expectance",
    "Freedom": "Freedom to make life choices",
    "Generosity": "Generosity",
    "Trust..Government.Corruption.": "Perceptions of corruption",
    "Trust (Government Corruption)": "Perceptions of corruption",
}


# Step 2: Load and clean all CSV files
all_files = glob.glob("../dataset/*.csv")  # loads all CSV files in dataset
dfs = []

for file in all_files:
    df = pd.read_csv(file)
    df = df.rename(columns=rename_map)  # rename columns to match the standard
    dfs.append(df)

# Step 3: Combine all CSVs
combined_df = pd.concat(dfs, ignore_index=True)

# Step 4: (Optional) Keep only the columns you care about, in consistent order
final_columns = [
    "Overall rank",
    "Country or region",
    "Score",
    "GDP per capita",
    "Social support",
    "Healthy life expectancy",
    "Freedom to make life choices",
    "Generosity",
    "Perceptions of corruption",
    "year"
]
combined_df = combined_df[final_columns]

# Step 5: Save the combined dataset
combined_df.to_csv("combined_happiness.csv", index=False)