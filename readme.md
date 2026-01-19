EcoPackAI 🌱
AI-Powered Sustainable Packaging Recommendation System

📌 Overview
EcoPackAI is a full-stack AI-driven web application that recommends eco-friendly packaging materials based on product attributes, cost efficiency, and environmental impact.

🏗️ Project Structure
ecopackai/
├── backend/
│   ├── app.py
│   ├── models/
│   │   ├── co2_model.pkl
│   │   └── cost_model.pkl
│   ├── database.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── index.css
│   │   └── components/
│   │       ├── Landing.js
│   │       ├── Login.js
│   │       ├── Predictor.js
│   │       ├── History.js
│   │       └── Dashboard.js
│   ├── package.json
│   └── .env
└── sample_data.csv


⚙️ Backend Setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py


🎨 Frontend Setup
cd frontend
npm install
npm start


🔐 Authentication
Google OAuth 2.0 for secure login
Manual email/password authentication (planned)

🤖 Machine Learning Models
Cost Prediction: Random Forest Regressor
CO₂ Impact Prediction: XGBoost Regressor

📊 Features
AI-powered packaging recommendations
Sustainability analytics dashboard
Cost vs CO₂ comparison
Secure authentication

🚀 Deployment
Backend: Render 
Database: PostgreSQL Cloud
Frontend: Netlify / Render

📌 Future Scope
Advanced analytics
Industry-level datasets
Automated sustainability reports


📜 License
This project is developed for academic purposes.
