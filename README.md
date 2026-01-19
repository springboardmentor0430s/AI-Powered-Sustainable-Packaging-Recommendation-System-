# EcoPackAI – Sustainable Packaging Recommendation System

EcoPackAI is an AI-powered web application that recommends eco-friendly and cost-effective packaging materials based on product requirements and sustainability factors. The system helps businesses reduce environmental impact while maintaining packaging quality and cost efficiency.

---

## Features
- AI-based packaging material recommendation
- Cost prediction using Machine Learning
- Carbon footprint (CO₂) estimation
- User-friendly web interface
- Secure backend with database integration

---

## Technologies Used
- Python
- Flask
- Machine Learning (Random Forest, XGBoost)
- PostgreSQL
- HTML, CSS, JavaScript

---

## Project Structure
EcoPackAI/
├── Dataset/
│   └── ecopack_food_packaging.csv     # Training dataset
│
├── models/
│   ├── cost_model.pkl                 # Trained cost prediction model
│   ├── co2_model.pkl                  # Trained CO₂ prediction model
│   └── scaler.pkl                     # Feature scaler
│
├── database/
│   └── db.py                          # PostgreSQL connection logic
│
├── templates/
│   ├── login.html                     # Login page
│   ├── signup.html                    # Registration page
│   ├── dashboard.html                 # Main dashboard
│   ├── analytics.html                 # Prediction analytics
│   └── history.html                   # Prediction history
│
├── static/
│   ├── style.css                      # Custom styles
│   └── bootstrap.min.css              # UI framework
│
├── app.py                             # Flask backend & ML inference
├── infosys.ipynb                      # Model training & experimentation
├── requirements.txt                  # Python dependencies
└── README.md



## How to Run
1. Clone the repository  
2. Install dependencies using `pip install -r requirements.txt`  
3. Configure PostgreSQL database  
4. Run the app using `python app.py`  

---
