# 🌿 EcoPackAI — AI-Powered Sustainable Packaging Recommendation System

An intelligent web-based system that predicts **packaging cost, CO₂ emissions**, and recommends **eco-friendly alternatives** based on user inputs.

---

## 🚀 Features

- 📦 Smart Packaging Input System  
- 🤖 AI-based Cost & CO₂ Prediction (ML Model)  
- ♻️ Sustainable Material Recommendation  
- 📊 Impact Analysis (Why prediction happened)  
- 📈 Best vs Average vs Worst Graphs  
- 🌍 Impact Insights Dashboard  
- 🕓 History Tracking  
- 🌙 Dark Mode UI  
- 📄 Export PDF (Impact Insights)

---

## 🧠 How It Works

1. User enters:
   - Material
   - Shape
   - Strength
   - Food Type
   - Quantity
   - Weight
   - Recyclability %

2. System:
   - Uses **Linear Regression Model**
   - Calculates **Cost & CO₂**
   - Applies rule-based logic for recommendation

3. Output:
   - 💰 Predicted Cost  
   - 🌱 CO₂ Emissions  
   - ♻️ Recommended Material  
   - 📊 Explanation (Impact Factors)

---

## 📊 Example Output
💰 Cost: ₹93.22
🌱 CO₂: 46.26 kg

Recommended: Bioplastic
Why: Low recyclability plastic → switch to biodegradable option.

---

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript, Chart.js  
- **Backend:** Flask (Python)  
- **ML Model:** Scikit-learn (Linear Regression)  
- **Data Handling:** NumPy  

---

## 📂 Project Structure

```
EcopackAI/
│
├── app.py
├── final_ecopack_data.csv
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── impact.html
│   └── history.html
│
├── static/
│   ├── style.css
│   ├── recommend.js
│   └── impact.js
```

---

## ⚙️ Installation & Setup

### 1. Clone Repository

git clone https://github.com/your-username/ecopack-ai.git

cd ecopack-ai


### 2. Install Dependencies

pip install flask numpy scikit-learn


### 3. Run the App

python app.py

## 🔐 Authentication
---

## 🔐 Login Credentials (Demo)


Email: mishrayashashree@gmail.com

Password: Mishra@123

Users need to **register first** to access the system.

### Steps:
1. Go to the Register page  
2. Create a new account  
3. Login using your registered credentials  

This ensures a simple user-based access system for the application.


---

## 📈 Key Highlights

- Real-time prediction system  
- Explainable AI (impact reasoning)  
- Sustainability-focused recommendations  
- Clean dashboard with analytics  
- Beginner-friendly ML integration  

---

## 🎯 Future Improvements

- 🔍 Advanced ML model (Random Forest / XGBoost)  
- 📦 Real packaging dataset integration  
- 🌐 Deployment (Render / AWS)  
- 📊 More detailed analytics  
- 👥 Multi-user authentication  

---

## 👩‍💻 Author

**Yashashree Mishra**  
Aspiring AI/ML Developer  

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share feedback!


