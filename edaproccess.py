#importing all the required packages
import pandas as pd
import numpy as np
import seaborn as sc
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.style.use("ggplot")
import os
from sklearn.preprocessing import RobustScaler
#Setting to see all the data without any ..... in middle
pd.set_option('display.max_columns', None)
pd.set_option('display.width',200000)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
#Reading the file
df=pd.read_csv("C:\\Users\\karna\\Documents\\finaldataset10000.csv")
#dealing with the size column
def convert_range_to_midpoint_or_preserve(value):

    if pd.isna(value) or isinstance(value, (int, float)):
        return value
    s = str(value).strip()
 
    if '-' in s:
        try:

            parts = s.split('-')
            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())
            return (min_val + max_val) / 2
        except:

            return np.nan

    numeric_check = pd.to_numeric(s, errors='coerce')

    if pd.notna(numeric_check):

        return numeric_check
    else:

        return value


df['toy_size'] = df['toy_size'].apply(convert_range_to_midpoint_or_preserve)
print("--- Step 1 Result (Mixed Types) ---")
#print(df['toy_size'].value_counts())
#print(df.describe())
def assign_final_size(value):
    #Converts numerical values to size strings and standardizes existing strings.

    if pd.isna(value):
        # Correctly handles NaN and exits the function
        return np.nan

    # This block executes ONLY if the value is NOT NaN
    if isinstance(value, (int, float)):
        if value <= 600:
            return 'Small'
        elif value <= 1200:
            return 'Medium'
        else:
            return 'Large'

    # This block handles string values
    if isinstance(value, str):
        s = value.lower().strip()
        if s in ['small', 's']:
            return 'Small'
        elif s in ['medium', 'm']:
            return 'Medium'
        elif s in ['large', 'big', 'l', 'extra large', 'extra-large', 'xl']: 
            return 'Large'
        else:
            # If the string is neither a recognized size nor a number, return NaN
            return np.nan

df['toy_size'] = df['toy_size'].apply(assign_final_size)
#Converting object data type to numeric
print("intial data types")
print(df.dtypes)
df["fragility_level"]=pd.to_numeric(df["fragility_level"],errors="coerce")
df["strength"]=pd.to_numeric(df["strength"],errors="coerce")
df["weight_capacity"]=pd.to_numeric(df["weight_capacity"],errors="coerce")
df["biodegradability_score"]=pd.to_numeric(df["biodegradability_score"],errors="coerce")
df["co2_emission_score"]=pd.to_numeric(df["co2_emission_score"],errors="coerce")
df["recyclability_percent"]=pd.to_numeric(df["recyclability_percent"],errors="coerce")
df["packaging_cost_inr"]=pd.to_numeric(df["packaging_cost_inr"],errors="coerce")
#bascic information about the data
print(df.head(5))
print(df.describe())
print(df.info())
print(df.isna().sum())
#Visualization of data using histogram
df.hist(figsize=(10,6))
plt.show()
#box plot for outliers sensing
plt.figure(figsize=(15,8))
sc.boxplot(data=df.select_dtypes(include="float64"))
plt.title("Outliers")
plt.show()
#heatmap initial for eda
#selecting numeric colums
df_numeric=df.select_dtypes(include="float64")
plt.figure(figsize=(10,6))
sc.heatmap(df_numeric.corr(),annot=True,cmap="coolwarm")
plt.title("Initial Corelation matrix For numeric Columns")
plt.xticks(rotation=0)
plt.show()
#optional counting values
'''for col in df.select_dtypes(include="object"):
     print('\n')
    print(col)
    print('\n')
    print(df[col].value_counts().sum())'''
# --- Handling Missing Values ---

# Impute original categorical column before encoding
df['recommended_packaging'] = df['recommended_packaging'].fillna(df['recommended_packaging'].mode()[0])

# Median imputation for skewed numeric features
median_cols = ['packaging_cost_inr', 'fragility_level', 'recyclability_percent']
for col in median_cols:
    df[col] = df[col].fillna(df[col].median())

# Mean imputation for normally distributed numeric features
mean_cols = ['biodegradability_score', 'co2_emission_score', 'weight_capacity']
for col in mean_cols:
    df[col] = df[col].fillna(df[col].mean())

print("\n--- Final NaN Check After Imputation ---")
print(df.isna().sum())

# --- Outlier Detection (Optional Logging) ---
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
outlier_counts = {}
outlier_rows_index = set()

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    mask = (df[col] < lower) | (df[col] > upper)
    outlier_counts[col] = mask.sum()
    outlier_rows_index.update(df[mask].index)

print("Outliers per column:")
for col, count in outlier_counts.items():
    print(f"{col}: {count}")
print("\nTotal rows with at least one outlier:", len(outlier_rows_index))
# Ensure target values are non-negative
df['co2_emission_score'] = df['co2_emission_score'].clip(lower=0)
df['packaging_cost_inr'] = df['packaging_cost_inr'].clip(lower=0)
# --- Scaling Numeric Features ---
scaler = RobustScaler()
numeric_cols = [col for col in df.select_dtypes(include=['int64', 'float64']).columns
                if col not in ['co2_emission_score', 'packaging_cost_inr']]
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

# --- Encoding Categorical Features ---

# Ordinal encoding for toy_size
size_mapping = {'Small': 1, 'Medium': 2, 'Large': 3}
df['toy_size_ordinal'] = df['toy_size'].map(size_mapping)
df = df.drop('toy_size', axis=1)
print("Feature 'toy_size' is Ordinal Encoded.")

# One-hot encoding for nominal categorical features
categorical_cols_to_encode = ['toy_material', 'recommended_packaging', 'toy_type']
df['packaging_name'] = df['recommended_packaging']
df = pd.get_dummies(df, columns=categorical_cols_to_encode, drop_first=True)

# --- Correlation Heatmap ---

# Define core features (adjust based on actual columns present)
core_features = [
    'fragility_level', 'strength', 'weight_capacity',
    'biodegradability_score', 'co2_emission_score',
    'recyclability_percent', 'packaging_cost_inr',
    'co2_impact_index', 'cost_efficiency_index',  # Optional: only if created earlier
    'toy_size_ordinal',
    'toy_material_4', 'toy_material_3', 'toy_material_5',
    'toy_material_Maple Wood', 'toy_material_ABS Plastic',
    'recommended_packaging_Recycled Box', 'recommended_packaging_Box',
    'recommended_packaging_Blister Pack', 'recommended_packaging_Recycled Bag',
    'recommended_packaging_Plastic Case'
]

# Filter only available features
available_features = [col for col in core_features if col in df.columns]
heatmap_df = df[available_features]

# Drop zero-variance columns and fill any remaining NaNs
heatmap_df = heatmap_df.loc[:, heatmap_df.std() != 0].fillna(0)

# Compute and plot correlation matrix
correlation_matrix = heatmap_df.corr()

plt.figure(figsize=(10, 8))
sc.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f",
    cmap='coolwarm',
    cbar=True,
    linewidths=.5,
    linecolor='black',
    annot_kws={"size": 8}
)
plt.title('Correlation Heatmap of Key Preprocessed Features', fontsize=16)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()
merge_map = {
    # Metal based
    'Tin Box': 'Metal Packaging',
    'Small Tin': 'Metal Packaging',
    'Metal Tin': 'Metal Packaging',

    # Cardboard based
    'Recycled Box': 'Cardboard Packaging',
    'Cardboard Box': 'Cardboard Packaging',
    'Cardboard Wrap': 'Cardboard Packaging',
    'Box': 'Cardboard Packaging',

    # Plastic based
    'Plastic Case': 'Plastic Packaging',
    'Plastic Tub': 'Plastic Packaging',
    'Polybag': 'Plastic Packaging',
    'Blister Pack': 'Plastic Packaging'
}

#Model 1 Regression model for co2 and cost
#X and y Definition
from sklearn.model_selection import train_test_split

X = df.drop(['co2_emission_score', 'packaging_cost_inr', 'toy_name', 'packaging_name'], axis=1)
y_reg = df[['co2_emission_score', 'packaging_cost_inr']]
#train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y_reg, test_size=0.2, random_state=42)

#Train MultiOutput Regression Model
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
reg_model = MultiOutputRegressor(RandomForestRegressor(n_estimators=200, random_state=42))
reg_model.fit(X_train, y_train)
#Evaluate Regression Model
from sklearn.metrics import mean_absolute_error, r2_score
y_pred = reg_model.predict(X_test)
print("MAE (CO2):", mean_absolute_error(y_test.iloc[:,0], y_pred[:,0]))
print("MAE (Cost):", mean_absolute_error(y_test.iloc[:,1], y_pred[:,1]))
print("R2 (CO2):", r2_score(y_test.iloc[:,0], y_pred[:,0]))
print("R2 (Cost):", r2_score(y_test.iloc[:,1], y_pred[:,1]))
X_test = X_test.copy()
X_test.index = y_test.index
#Evaluate Regression Model
from sklearn.preprocessing import RobustScaler, MinMaxScaler
def recommend_top5_packaging(X_input, original_df, top_n=5):
    # Predict CO2 and Cost using the trained multi-output model
    predicted = reg_model.predict(X_input)
    predicted_co2 = np.clip(predicted[:, 0], 0, None)
    predicted_cost = np.clip(predicted[:, 1], 0, None)
    
    # Create temporary DataFrame
    temp = pd.DataFrame({
        'packaging_name': original_df.loc[X_input.index, 'packaging_name'],
        'predicted_co2': predicted_co2,
        'predicted_cost': predicted_cost
    })

    # Normalize CO2 and Cost
    scaler = MinMaxScaler()
    temp[['co2_norm', 'cost_norm']] = scaler.fit_transform(
        temp[['predicted_co2', 'predicted_cost']]
    )

    # Sustainability score
    alpha, beta = 0.7, 0.3
    temp['sustainability_score'] = (
        alpha * temp['co2_norm'] + beta * temp['cost_norm']
    )

    # Sort and return Top-N
    top_recommendations = (
    temp.sort_values('sustainability_score')
        .drop_duplicates(subset='packaging_name')
        .head(top_n)
)

    return top_recommendations
top5_packages = recommend_top5_packaging(X_test, df.loc[X_test.index])

print("🌱 Top 5 Eco-Friendly Packaging Recommendations")
print(top5_packages)
print("Sample predictions:\n", reg_model.predict(X_test[:5]))
import pickle

# Save trained regression model
pickle.dump(reg_model, open("reg_model.pkl", "wb"))

# Save feature scaler (RobustScaler used before training)
pickle.dump(scaler, open("feature_scaler.pkl", "wb"))

# Save training feature columns
pickle.dump(X.columns.tolist(), open("feature_columns.pkl", "wb"))

print("✅ Model and preprocessors saved successfully")
