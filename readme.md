# EcoPackAI 🌱

## AI‑Powered Sustainable Packaging Recommendation System

---

## 1. Introduction

EcoPackAI is a full‑stack, AI‑driven web application designed to assist businesses and researchers in selecting **sustainable and cost‑effective packaging materials**. The system leverages **machine learning models** to predict **carbon dioxide (CO₂) emissions** and **cost implications** based on product attributes, and recommends the most eco‑friendly packaging alternatives accordingly.

This project has been developed as part of an **academic internship / coursework**, with an emphasis on practical implementation of **AI, web technologies, and database integration**.

---

## 2. Problem Statement

Packaging industries face increasing pressure to reduce environmental impact while maintaining cost efficiency and structural integrity. Traditional material selection methods rely heavily on manual assessment, lacking predictive intelligence and sustainability analytics.

There is a need for an **intelligent decision‑support system** that:

* Predicts environmental impact quantitatively
* Compares cost vs sustainability trade‑offs
* Recommends optimal eco‑friendly packaging materials

---

## 3. Objectives

* To develop a web‑based system for sustainable packaging recommendations
* To apply machine learning models for CO₂ and cost prediction
* To provide an interactive dashboard for sustainability analytics
* To integrate secure user authentication and data persistence

---

## 4. System Architecture

EcoPackAI follows a **client–server architecture**:

* **Frontend**: React.js (User Interface & Visualization)
* **Backend**: Flask (REST API & ML inference)
* **Database**: PostgreSQL (Prediction history & user data)
* **ML Models**: Trained regression models for cost and CO₂ estimation

```
User → React Frontend → Flask API → ML Models / PostgreSQL → Response → UI
```

---

## 5. Project Structure

```
Ecopackai/
│── backend/
│   │── app.py
│   │── database.py
│   │── requirements.txt
│   │── models/
│   │   │── co2_model.pkl
│   │   │── cost_model.pkl
│
│── frontend/
│   │── public/
│   │   │── index.html
│   │── src/
│   │   │── components/
│   │   │   │── Landing.js
│   │   │   │── Login.js
│   │   │   │── Predictor.js
│   │   │   │── History.js
│   │   │   │── Dashboard.js
│   │   │── App.js
│   │   │── index.js
│   │   │── index.css
│   │── package.json
│
│── .gitignore
│── README.md
```

---

## 6. Machine Learning Models

Two supervised regression models are used:

### 6.1 CO₂ Impact Prediction

* Model Type: **XGBoost Regressor**
* Purpose: Predicts estimated CO₂ emissions based on material properties

### 6.2 Cost Prediction

* Model Type: **Random Forest Regressor**
* Purpose: Predicts manufacturing and material cost

### 6.3 Input Features

* Material Strength (MPa)
* Weight Capacity (kg)
* Biodegradability (%)
* Recyclability (%)

---

## 7. Backend Setup

### Prerequisites

* Python 3.9+
* PostgreSQL

### Steps

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs at:

```
http://localhost:5000
```

---

## 8. Frontend Setup

### Prerequisites

* Node.js 18+

### Steps

```bash
cd frontend
npm install
npm start
```

Frontend runs at:

```
http://localhost:3000
```

---

## 9. Authentication

* Google OAuth 2.0 is integrated for secure login
* Manual email/password authentication is planned as a future enhancement

---

## 10. Key Features

* AI‑based sustainable material recommendations
* Cost vs CO₂ comparison
* Interactive dashboard and analytics
* Prediction history tracking
* Secure authentication

---

## 11. Deployment

* **Backend**: Render
* **Database**: PostgreSQL (Cloud)
* **Frontend**: Netlify / Render

---

## 12. Future Scope

* Industry‑scale datasets
* Automated sustainability reports
* Advanced analytics and visualization
* Multi‑criteria decision optimization

---


