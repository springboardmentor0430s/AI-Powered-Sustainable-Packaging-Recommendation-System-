# EcoPackAI – AI-Powered Sustainable Packaging Recommendation System

## Project Overview

**EcoPackAI** is a Flask-based web application that recommends sustainable and cost-efficient packaging materials using machine learning.  The system predicts **packaging cost** and **CO₂ environmental impact** based on product attributes, helping businesses make environmentally responsible packaging decisions.

The application integrates machine learning models with a user-friendly web interface, prediction history tracking, and a basic analytics dashboard.

---

## Project Objectives

- Promote eco-friendly packaging alternatives  
- Reduce environmental impact through data-driven decisions  
- Apply machine learning to real-world sustainability challenges  
- Build an end-to-end AI web application using Flask  

---

## Key Features

- **Machine Learning Predictions**  
  Random Forest models predict packaging cost and CO₂ footprint  

- **Sustainability Insights**  
  Compare materials based on cost efficiency and environmental impact  

- **User Authentication**  
  Signup and login with session-based authentication  

- **Dashboard & History**  
  View previous predictions and sustainability insights  

- **CSV Export**  
  Download prediction history for reporting  

- **Responsive UI**  
  Built using HTML, CSS, Bootstrap, and custom styling  

---

## System Architecture

```

User Interface Layer
        ↓
Flask Backend API
        ↓
AI / ML Layer (Random Forest Models)
        ↓
Database Layer
        ↓
Business Intelligence Dashboard

```

---

## Project Structure

```

EcoPackAI/
│
├── model/                    # Trained ML assets
│   ├── feature_columns.pkl   # Model input features
│   ├── rf_cost.pkl           # Cost prediction model
│   ├── rf_co2.pkl            # CO₂ prediction model
│   └── scaler.pkl            # Feature scaler
│
├── static/
│   ├── css/
│   │   └── style.css         # Application styling
│   └── images/
│       └── eco.png
│
├── templates/
│   ├── base.html             # Base layout
│   ├── index.html            # Landing page
│   ├── login.html            # User login
│   ├── signup.html           # User registration
│   ├── dashboard.html        # User dashboard
│   ├── predict.html          # Input form for predictions
│   ├── result.html           # Prediction results
│   └── history.html          # Prediction history
│
├── app.py                    # Flask app & ML inference
├── db.py                     # Database logic
├── requirements.txt
└── README.md

````

---

## Machine Learning Details

- **Algorithm:** Random Forest Regressor  
- **Prediction Targets:**
  - Packaging Cost  
  - CO₂ Emission Score  

- **Workflow:**
  1. Data preprocessing and feature engineering  
  2. Feature scaling  
  3. Model training and evaluation  
  4. Model serialization using Joblib  
  5. Real-time inference through Flask backend  

---

## Application Functionality

- **Authentication Pages:** Signup and login  
- **Prediction Form:** User inputs product details  
- **Results Page:** Displays predicted cost and CO₂ impact  
- **Dashboard:** Sustainability overview  
- **History Page:** Stores and displays past predictions  
- **Export:** Download prediction history as CSV  

---

## Installation & Setup

### Prerequisites
- Python 3.8+  
- Git  
- Virtual environment (recommended)  

### Steps

```bash
git clone https://github.com/springboardmentor0430s/AI-Powered-Sustainable-Packaging-Recommendation-System-.git
cd AI-Powered-Sustainable-Packaging-Recommendation-System-
````

```bash
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
```

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## API Endpoints

| Endpoint       | Method | Description             |
| -------------- | ------ | ----------------------- |
| `/predict`     | POST   | Web-based prediction    |
| `/api/predict` | POST   | JSON-based prediction   |
| `/history`     | GET    | User prediction history |
| `/export/csv`  | GET    | Export prediction data  |

---

## Security

* Session-based authentication
* Password hashing
* Parameterized database queries
* Flask session handling

---
