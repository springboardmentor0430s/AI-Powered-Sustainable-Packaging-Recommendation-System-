# EcoPackAI - AI-Powered Sustainable Packaging Solution

> An intelligent system that provides AI-driven recommendations for eco-friendly packaging materials with comprehensive environmental impact analytics.

## 🌿 Overview

EcoPackAI is a full-stack web application that helps businesses find sustainable packaging solutions by:
- Analyzing product specifications using AI algorithms
- Recommending eco-friendly materials based on environmental impact
- Computing detailed environmental scores (CO₂ reduction, cost savings, recyclability)
- Providing comprehensive analytics and sustainability reports
- Tracking environmental improvements over time

---

## ✨ Features

### 🎯 Core Functionality

#### 1. **Smart Product Analysis**
- Input product details (name, category, weight, fragility, temperature sensitivity)
- AI algorithm analyzes product requirements
- Returns ranked list of sustainable packaging options
- Real-time preview of product specifications

#### 2. **AI Material Recommendations**
- 8+ eco-friendly materials in database:
  - Recycled Plastic
  - Biodegradable Plastic (PLA)
  - Kraft Paper
  - Corrugated Cardboard
  - Mushroom Leather
  - Bamboo Fiber
  - Cork
  - Glass

#### 3. **Environmental Score Computation**
- **Eco-Score**: Composite environmental rating (0-100)
- **Carbon Footprint**: CO₂ emissions per unit weight
- **Sustainability Rating**: Comprehensive environmental metrics
- **CO₂ Reduction**: Percentage vs. baseline plastic
- **Cost Savings**: Economic benefits calculation
- **Recyclability Index**: Post-consumer recyclability percentage
- **Biodegradability Score**: Natural decomposition rating

#### 4. **Advanced Analytics Dashboard**
- Real-time metrics display with animations
- CO₂ reduction trends (line chart)
- Material usage distribution (pie chart)
- Cost savings analysis
- Monthly trend analysis
- Material usage insights
- Time-period filters (week, month, all-time)

#### 5. **Export & Reporting**
- **PDF Reports**: Comprehensive sustainability reports with tables and metrics
- **Excel Export**: Detailed recommendation data
- **CSV Export**: Raw data export for analysis
- Charts and visualizations included

#### 6. **Material Comparison**
- Side-by-side comparison of materials
- Detailed metrics for each material
- Environmental benefits comparison
- Cost analysis

#### 7. **User Management**
- Secure registration and login (JWT authentication)
- Password hashing with Werkzeug
- Session management
- User-specific data isolation

---

## 🚀 Advanced Features

### UI/UX Enhancements
- **Smooth Animations**: SlideIn, CountUp, Pulse, Shimmer effects
- **Interactive Forms**: Real-time preview, dynamic sliders
- **Responsive Design**: Mobile-first Bootstrap layout
- **Dark/Light Elements**: Gradient backgrounds, smooth transitions
- **Loading States**: Animated spinners and loading indicators
- **Card Hover Effects**: Translatey, scale, shadow animations

### Analytics Capabilities
- **Comprehensive Metrics**: Total CO₂, cost savings, recommendation count
- **Material Breakdown**: Usage frequency, average metrics per material
- **Monthly Trends**: Historical data analysis
- **Insights Generation**: Automatic pattern recognition
- **Period Analysis**: Filter by week, month, or all-time

### API Features
- **RESTful Architecture**: Clean endpoint design
- **JWT Authentication**: Secure token-based auth
- **Input Validation**: Comprehensive data validation
- **Error Handling**: Detailed error messages
- **Pagination Support**: Ready for large datasets
- **Rate Limiting Ready**: Built for scalability

---

## 📋 Architecture

### Backend Stack
- **Framework**: Flask 2.3.3
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login + Flask-JWT-Extended
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly (interactive charts)
- **Reporting**: ReportLab (PDF generation)
- **Security**: CORS, JWT tokens, password hashing

### Frontend Stack
- **Template Engine**: Jinja2
- **UI Framework**: Bootstrap 5
- **Styling**: Custom CSS with animations
- **Charting**: Plotly.js
- **Icons**: Font Awesome 6
- **Interactivity**: Vanilla JavaScript

### Database Schema
```
users
├── id (PK)
├── username (unique)
├── email (unique)
├── password_hash
└── created_at

products
├── id (PK)
├── user_id (FK → users)
├── product_name
├── category
├── weight_kg
├── fragility_level
├── temperature_sensitive
└── created_at

materials
├── id (PK)
├── material_name
├── strength_rating
├── weight_capacity_kg
├── biodegradability_score
├── recyclability_percent
├── co2_emission_score
└── cost_per_kg

recommendations
├── id (PK)
├── user_id (FK → users)
├── product_id (FK → products)
├── material_id (FK → materials)
├── recommendation_score
├── co2_reduction_percent
├── cost_savings_percent
└── created_at
```

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip and virtualenv

### Setup Steps

1. **Clone Repository**
```bash
cd c:\Users\Kavita\Desktop\eco pack
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Create .env File**
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/ecopackai
JWT_SECRET_KEY=your_super_secret_key_here
SECRET_KEY=another_secret_key
DEBUG=True
```

4. **Initialize Database**
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>>     # Materials will auto-seed
```

5. **Run Application**
```bash
python app.py
```

6. **Access Application**
```
Frontend: http://localhost:5000
API Docs: See API_DOCUMENTATION.md
```

---

## 📚 API Endpoints Summary

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout user

### Recommendations
- `POST /api/recommendations/recommend` - Get AI recommendations
- `POST /api/recommendations/environmental-score` - Calculate eco-scores
- `POST /api/recommendations/compare` - Compare materials
- `GET /api/recommendations/history` - Get recommendation history
- `GET /api/recommendations/materials` - List all materials

### Analytics
- `GET /api/analytics/dashboard` - Dashboard metrics
- `GET /api/analytics/metrics/comprehensive` - Comprehensive metrics
- `GET /api/analytics/metrics/period?period={week|month|all}` - Period metrics
- `GET /api/analytics/insights/materials` - Material insights
- `GET /api/analytics/export/csv` - Export as CSV
- `GET /api/analytics/export/excel` - Export as Excel
- `GET /api/analytics/export/pdf` - Export as PDF
- `GET /api/analytics/export/report/pdf` - Detailed PDF report

---

## 📊 Module Breakdown

### Module 1-2: Authentication & Core Infrastructure ✅
- User registration and secure login
- JWT token authentication
- Database setup with PostgreSQL
- SQLAlchemy models and relationships

### Module 3-4: Product Input & Recommendations ✅
- Product input form with validation
- AI scoring algorithm
- Environmental impact calculations
- Material recommendation engine

### Module 5-6: REST APIs & Frontend ✅
- Complete REST API implementation
- JSON response structures
- Secure endpoint authentication
- HTML/CSS/Bootstrap UI
- Interactive JavaScript
- Responsive design

### Module 7: Business Intelligence Dashboard ✅
- Analytics dashboard with metrics
- Plotly interactive charts
- CO₂ reduction trends
- Cost savings analysis
- Material usage visualization
- PDF/Excel export reports
- Monthly trend analysis
- Material insights

---

## 🎨 UI Components

### Pages Implemented
- ✅ **Login/Signup** - Secure authentication pages
- ✅ **Dashboard** - Main hub with navigation
- ✅ **Product Input** - Advanced form with preview
- ✅ **Recommendations** - Card and table views
- ✅ **Analytics** - Interactive dashboard with charts
- ✅ **Reports** - Exportable sustainability reports

### Animation & Effects
- Slide-in animations on page load
- Count-up animations for metrics
- Hover effects on cards and buttons
- Pulse animations for loading states
- Shimmer effects for emphasis
- Smooth transitions on all interactions
- Scale transforms on hover
- Gradient backgrounds

---

## 🔐 Security Features

- ✅ Password hashing (Werkzeug bcrypt)
- ✅ JWT token authentication
- ✅ CORS configuration
- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ User data isolation
- ✅ Secure session management
- ✅ HTTPS ready configuration

---

## 📈 Performance Optimizations

- Database query optimization with indexes
- Lazy loading relationships
- Response compression ready
- Asset minification support
- Efficient pagination structure
- Caching structure in place
- API response optimization

---

## 🧪 Testing

### Recommended Test Scenarios

1. **User Registration**
```bash
POST /api/auth/register
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

2. **User Login**
```bash
POST /api/auth/login
{
  "username": "testuser",
  "password": "password123"
}
```

3. **Product Analysis**
```bash
POST /api/recommendations/recommend
{
  "product_name": "Test Product",
  "category": "Food",
  "weight_kg": 0.5,
  "fragility_level": 3,
  "temperature_sensitive": false
}
```

4. **Export Report**
```bash
GET /api/analytics/export/report/pdf
```

---

## 📦 Dependencies

```
Core Framework:
- Flask==2.3.3
- Flask-SQLAlchemy==3.0.5
- Flask-Login==0.6.2
- Flask-CORS==4.0.0
- Flask-JWT-Extended==4.5.3

Database:
- psycopg2-binary==2.9.9
- SQLAlchemy (via Flask-SQLAlchemy)

Data Processing:
- pandas==2.0.3
- numpy==1.24.3

Visualization:
- plotly==5.16.1

Reporting:
- reportlab==4.0.8
- openpyxl==3.1.2
- xlsxwriter==3.1.2

Utilities:
- python-dotenv==1.0.0
- Werkzeug==2.3.7
- requests==2.31.0
```

---

## 🚦 Getting Started

### 1. First Run Checklist
- [ ] Clone repository
- [ ] Install dependencies
- [ ] Setup PostgreSQL database
- [ ] Create .env file with credentials
- [ ] Run `python app.py`
- [ ] Navigate to http://localhost:5000
- [ ] Register new account
- [ ] Analyze your first product

### 2. Test Features
- [ ] Create multiple product analyses
- [ ] View recommendations
- [ ] Compare materials
- [ ] View analytics dashboard
- [ ] Export CSV/Excel/PDF
- [ ] Check material insights

---

## 📝 Project Structure

```
eco pack/
├── app.py                          # Main Flask app
├── auth.py                         # Authentication routes
├── recommendations.py              # Recommendation API
├── analytics.py                    # Analytics API
├── models.py                       # Database models
├── database.py                     # SQLAlchemy setup
├── config.py                       # Configuration
├── requirements.txt                # Dependencies
├── .env                           # Environment variables
├── API_DOCUMENTATION.md           # API reference
├── static/
│   ├── css/
│   │   └── style.css              # Main styling with animations
│   └── js/
│       └── main.js                # JavaScript utilities
└── templates/
    ├── base.html                  # Base template
    ├── index.html                 # Home page
    ├── login.html                 # Login page
    ├── signup.html                # Registration page
    ├── dashboard.html             # Dashboard
    ├── product_input.html         # Product input form (ENHANCED)
    ├── recommendations.html       # Recommendations page (ENHANCED)
    ├── analytics.html             # Analytics dashboard (ENHANCED)
    ├── report.html                # Report page
    └── recommendations_new.html   # New recommendations view
```

---

## 🎯 Milestones

- **Week 1-2**: ✅ Core setup, authentication, database
- **Week 3-4**: ✅ REST APIs, recommendations engine
- **Week 5-6**: ✅ Frontend UI, Bootstrap integration
- **Week 7-8**: ✅ Analytics dashboard, reporting, advanced features

---

## 🤝 Contributing

To contribute to this project:
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

---

## 📞 Support

For issues or questions:
1. Check API_DOCUMENTATION.md
2. Review inline code comments
3. Check error messages in browser console
4. Review application logs

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 🌍 Environmental Impact

This application helps businesses:
- **Reduce CO₂ emissions** by up to 90% through smart packaging choices
- **Save costs** while improving sustainability
- **Track environmental progress** with detailed metrics
- **Make data-driven decisions** about packaging materials
- **Report sustainability** improvements to stakeholders

---

## ✅ Checklist: All Modules Implemented

- ✅ **Module 1-2**: User authentication and core infrastructure
- ✅ **Module 3**: Product input handling with validation
- ✅ **Module 4**: AI material recommendation engine
- ✅ **Module 5**: REST APIs with JSON responses
- ✅ **Module 5**: PostgreSQL database integration
- ✅ **Module 5**: Secure JWT authentication
- ✅ **Module 6**: Frontend UI with HTML/CSS/Bootstrap
- ✅ **Module 6**: Interactive forms and displays
- ✅ **Module 6**: Ranking table and comparison metrics
- ✅ **Module 7**: Business intelligence dashboard
- ✅ **Module 7**: CO₂ reduction % tracking
- ✅ **Module 7**: Cost savings analysis
- ✅ **Module 7**: Material usage trends with Plotly
- ✅ **Module 7**: PDF/Excel export reports
- ✅ **BONUS**: Advanced animations and effects
- ✅ **BONUS**: Environmental score computation API
- ✅ **BONUS**: Material comparison API
- ✅ **BONUS**: Comprehensive analytics endpoints
- ✅ **BONUS**: Time-period based filtering
- ✅ **BONUS**: Material insights generation
- ✅ **BONUS**: Enhanced UI/UX with smooth animations

---

**Last Updated**: January 19, 2026  
**Version**: 1.0.0  
**Status**: Production Ready ✅

