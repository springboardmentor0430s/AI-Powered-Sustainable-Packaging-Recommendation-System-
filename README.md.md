EcoPackAI – AI-Powered Sustainable Packaging Recommendation System Project Overview



EcoPackAI is an AI-powered system designed to recommend eco-friendly and cost-effective packaging materials based on product attributes such as size, fragility, material type, and sustainability metrics.

The project combines Machine Learning, Python backend processing, and a frontend interface to support data-driven decisions for sustainable packaging.



Repository Structure \& Folder Explanation

project/

│

├── backend/

├── data/

├── edaprocess.py

├── frontend.html

├── pandas.cpython-311.pyc

└── README.md



#### **backend/**



This folder contains all server-side and machine learning components.



Purpose:



Handle ML model loading



Feature scaling and prediction logic



Backend processing for recommendations



Contents:



app.py



Main backend application file



Handles model inference and packaging recommendations



##### **reg\_model.pkl**



Trained Machine Learning regression model



Used to predict packaging cost / suitability



##### **feature\_scaler.pkl**



Scaler used during model training



Ensures consistent feature scaling during predictions



##### **feature\_columns.pkl**



Stores feature column structure used during training



Helps align new input data correctly



Technologies Used:



Python



Scikit-learn



Pickle (model serialization)



NumPy



Pandas



#### **data/**



This folder contains the dataset used for training and analysis.



Contents:



finaldataset10000.csv



Dataset with ~10,000 rows



Includes product attributes, sustainability scores, and recommended packaging



Purpose:



Exploratory Data Analysis (EDA)



Model training



Validation and testing



Technologies Used:



CSV format



Pandas



Excel-compatible data handling



#### **edaprocess.py**



Purpose:



Performs Exploratory Data Analysis (EDA)



Cleans and preprocesses raw data



Handles:



Missing values



Data type conversions



Feature selection



Statistical summaries



Technologies Used:



Python



Pandas



NumPy



Matplotlib / Seaborn (if used)



#### **frontend.html**



Purpose:



Frontend user interface



Allows users to input product details



Displays packaging recommendations



Technologies Used:



HTML



CSS



JavaScript (basic client-side logic)





#### **Technologies \& Tools Used Programming Languages**

#### 

Python



HTML



JavaScript



Libraries \& Frameworks



Pandas



NumPy



Scikit-learn



Pickle



Tools



Git \& GitHub



Git Bash



VS Code



#### 

#### **Concepts Applied**



Machine Learning (Regression)



Feature Engineering



Data Preprocessing



Model Serialization



Sustainable AI Decision Support



#### **Workflow Summary**



Dataset collected and cleaned



Exploratory Data Analysis performed



Features engineered and scaled



ML model trained and saved



Backend loads model for predictions



Frontend provides user interaction



Recommendations generated based on input







