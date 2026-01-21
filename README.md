# **AI-Powered Sustainable Packaging Recommendation System**


## Overview

EcoPackAI is an intelligent packaging optimization platform that leverages machine learning to recommend sustainable, cost-effective packaging alternatives. The system analyzes material properties, environmental impact, and cost factors to provide data-driven recommendations for businesses seeking to reduce their carbon footprint while maintaining cost efficiency.

### Key Features

- **ML-Powered Predictions**: XGBoost models optimized with Optuna for accurate cost and CO₂ impact predictions
- **AI Chatbot Assistant**: Gemini 2.5 Flash integration for natural language insights and comparisons
- **Real-time Analytics**: Interactive dashboards with comprehensive sustainability metrics
- **Bulk Processing**: Upload CSV/Excel files for batch analysis
- **Secure Authentication**: OAuth 2.0 (Google) and JWT-based authentication
- **Responsive Design**: Modern UI optimized for desktop and mobile devices

---

## Architecture

```
EcoPackAI/
├── Dataset/
│   └── ecopack.xlsx               # Training dataset
├── models/
│   ├── final_cost_model.pkl       # Trained cost prediction model
│   ├── final_co2_model.pkl        # Trained CO₂ prediction model
│   ├── label_encoders.pkl         # Encoders for categorical features
│   ├── cost_features.txt          # Feature list for cost model
│   ├── co2_features.txt           # Feature list for CO₂ model
│   ├── feature_metadata.json      # Feature descriptions and ranges
│   └── feature_documentation.txt  # Human-readable feature explanation
├── templates/
│   ├── index.html                 # Login interface
│   └── dashboard.html             # BI dashboard view
├── uploads/                       # Bulk upload files
├── app.py                         # Flask application (backend + inference)
├── Ecopack.ipynb                  # Model training & experimentation
├── README.md
└── requirements.txt
```

---

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Google OAuth credentials
- Gemini API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/springboardmentor0430s/AI-Powered-Sustainable-Packaging-Recommendation-System-.git
cd AI-Powered-Sustainable-Packaging-Recommendation-System-
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file:
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key
```

5. **Initialize database**
```bash
python app.py
```

6. **Run the application**
```bash
# Development
flask run

# Production (Gunicorn)
gunicorn app:app --workers 4 --bind 0.0.0.0:5000
```

---

## Key Technologies

### Backend
- **Flask**: Web framework
- **PostgreSQL**: Database with JSONB support
- **XGBoost**: Gradient boosting models
- **Scikit-learn**: ML pipeline
- **Pandas/NumPy**: Data processing

### AI/ML
- **XGBoost 2.0+**: Primary ML algorithm (both models)
  - Cost: Optuna-optimized (R²=0.9749)
  - CO₂: Manually-tuned (R²=0.9955)
- **Optuna 3.5+**: Bayesian hyperparameter optimization (50 trials)
- **Scikit-learn 1.3+**: Preprocessing, cross-validation, metrics
- **SHAP 0.44+**: Feature importance analysis
- **Google Gemini 2.5 Flash**: Conversational AI chatbot
- **Joblib**: Model serialization

### Frontend
- **Vanilla JavaScript**: No framework overhead
- **Tailwind CSS**: Utility-first styling
- **Chart.js**: Data visualizations
- **Responsive Design**: Mobile-first approach

### Security
- **bcrypt**: Password hashing
- **JWT**: Token-based auth
- **OAuth 2.0**: Google sign-in
- **CORS**: Cross-origin security

---

## API Endpoints

### Authentication
```
POST   /api/register              # User registration
POST   /api/login                 # Email/password login
GET    /auth/google               # OAuth login
POST   /api/logout                # Logout
```

### Recommendations
```
POST   /api/recommend             # Get packaging alternatives
POST   /api/compare               # Compare materials
POST   /api/bulk-upload           # Batch processing
```

### Analytics
```
GET    /api/analytics/user        # User statistics
GET    /api/history               # Recommendation history
POST   /api/analytics/compare     # AI chatbot queries
GET    /api/analytics/smart-insights  # Auto-generated insights
```

### Utilities
```
GET    /api/materials             # Available materials
GET    /api/features              # Model features
```

---

## Features in Detail

### 1. Smart Recommendations
- Analyzes 6 material types: Plastic, Paper, Cardboard, Glass, Metal, Aluminium
- Considers 20+ shape types: Bottle, Box, Bag, Can, Jar, etc.
- Provides 5 ranked alternatives per request
- Volume-based pricing (up to 30% discount)

### 2. AI Chatbot
- Natural language queries
- Intent-based responses (cost vs. sustainability)
- Historical data analysis
- Multi-material comparisons

### 3. Analytics Dashboard
- Cost savings tracker
- CO₂ reduction metrics
- Material usage trends
- Export capabilities

### 4. Bulk Processing
- CSV/Excel upload support
- Batch predictions (100+ rows)
- Detailed results export
- Error handling

## Deployment

### Render (Recommended)
```bash
# Set environment variables in Render dashboard
# Deploy from GitHub repository
# Auto-deploy on push to main branch
```
