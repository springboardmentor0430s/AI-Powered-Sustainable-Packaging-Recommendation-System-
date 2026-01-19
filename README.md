Milestone 3: Backend \& Database Integration (Completed) ✅

Status: 100% Complete.

Database Connectivity: Successfully established a connection between the Flask backend and PostgreSQL database (eco\_materials\_db).

Data Persistence: AI predictions, including optimized cost, CO2 levels, and sustainability scores, are now being saved in real-time into the ai\_predictions table.

API Structure: Implemented a standardized JSON response structure for seamless communication between the frontend and backend.

Verification: Database entries have been verified via pgAdmin with successful record insertion (Current row count: 68+).

Milestone 4: Full-Stack AI Integration & Final Submission
Project Overview
This milestone marks the completion of the AI-Powered Sustainable Packaging Recommendation System. The system now features a fully integrated backend, an AI ranking engine, and a persistent database to help users choose eco-friendly packaging materials.
Key Features Implemented
AI Ranking Engine: Integrated a trained XGBoost model to rank packaging materials based on sustainability scores, CO2 emission levels, and cost-effectiveness.
Flask Backend: Developed a robust Flask API to handle user inputs and fetch real-time predictions from the ML model.
PostgreSQL Persistence: Successfully connected the application to a PostgreSQL database (eco_materials_db) to store user queries and AI-generated recommendations for future analysis.
Frontend Dashboard: Created an intuitive UI using HTML templates to display recommended materials and their environmental impact metrics.
Technical Stack
Backend: Python, Flask
AI/ML: XGBoost, Scikit-learn
Database: PostgreSQL
Frontend: HTML5, CSS3
How to Run
Clone the repository and switch to the Rajnandini_EcoPackAI branch.
Install dependencies: pip install -r requirements.txt.
Set up the PostgreSQL database connection in app.py.
Run the application: python app.py.

Successful Deployment: The application is fully functional and has been successfully deployed on the Render platform.
Live URL: https://ecopack-ai-live.onrender.com
