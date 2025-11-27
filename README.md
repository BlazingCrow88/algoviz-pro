# AlgoViz Pro - Algorithm Visualization Platform

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Django](https://img.shields.io/badge/django-5.2-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A comprehensive web-based platform for visualizing sorting and searching algorithms,
analyzing Python code complexity, and integrating with GitHub repositories.

**INF601 - Advanced Programming with Python**  
**Student:** Brian Shoemaker  
**Concentration:** Computer Science

---

## 🎯 Features

### Algorithm Visualization
- **Sorting Algorithms:** Bubble Sort, Merge Sort, Quick Sort
- **Searching Algorithms:** Binary Search, Linear Search, Breadth-First Search
- **Interactive Controls:** Play, Pause, Step-by-step execution
- **Real-time Statistics:** Comparisons, swaps, time complexity
- **HTML5 Canvas Visualization:** Smooth animations

### GitHub Integration
- Search repositories by keyword and language
- Fetch Python files from any public repository
- Automatic response caching
- Rate limit management
- Error handling with retries

### Code Analysis
- Cyclomatic complexity calculation
- Maintainability index (0-100)
- Function-level metrics
- Nesting depth analysis
- Code quality recommendations

---

## 📋 Requirements

- Python 3.9 or higher
- pip (Python package manager)
- Git

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/algoviz-pro.git
cd algoviz-pro
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ in your browser.

---

## 📁 Project Structure
```
algoviz-pro/
├── algorithms/ # Algorithm implementations
├── visualization/ # Web interface
├── github_integration/ # GitHub API client
├── analytics/ # Code complexity analyzer
├── templates/ # HTML templates
├── static/ # CSS, JavaScript, images
├── docs/ # Documentation
└── manage.py # Django management script
```

---

## 🎓 Algorithm Complexity Reference

| Algorithm     | Best Case  | Average    | Worst Case | Space    | Stable |
|---------------|------------|------------|------------|----------|--------|
| Bubble Sort   | O(n)       | O(n²)      | O(n²)      | O(1)     | Yes    |
| Merge Sort    | O(n log n) | O(n log n) | O(n log n) | O(n)     | Yes    |
| Quick Sort    | O(n log n) | O(n log n) | O(n²)      | O(log n) | No     |
| Binary Search | O(1)       | O(log n)   | O(log n)   | O(1)     | N/A    |
| Linear Search | O(1)       | O(n)       | O(n)       | O(1)     | N/A    |

---

## 💻 Usage

### Visualizing Algorithms

1. Navigate to **Visualize** page
2. Select an algorithm from the dropdown
3. Enter a comma-separated array (e.g., `5,2,8,1,9`)
4. Click **Execute**
5. Use Play/Pause/Step controls to watch the visualization

### Searching GitHub

1. Navigate to **GitHub** page
2. Enter search query (e.g., "django")
3. Select language filter (default: Python)
4. Click **Search**
5. View repository details and fetch Python files

### Analyzing Code

1. Navigate to **Analytics** page
2. Paste Python code or upload a file
3. Click **Analyze**
4. View complexity metrics and recommendations

---

## 🧪 Running Tests
```bash
python manage.py test
```

---

## 📊 Technologies Used

- **Backend:** Django 5.2.7
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **Visualization:** HTML5 Canvas API
- **Code Analysis:** Python AST module
- **API Integration:** GitHub REST API v3

---

## 🏗️ Architecture

### Django Apps

1. **algorithms/** - Algorithm implementations and execution
2. **visualization/** - Web pages and visualization interface
3. **github_integration/** - GitHub API client with caching
4. **analytics/** - Code complexity analysis using AST

### Design Patterns

- **MTV (Model-Template-View)** - Django's architecture pattern
- **Repository Pattern** - GitHub API client abstraction
- **Strategy Pattern** - Interchangeable algorithm implementations

---

## 📝 Development

### Adding a New Algorithm

1. Create algorithm class in `algorithms/sorting.py` or `algorithms/searching.py`
2. Implement `sort()` or `search()` method as generator
3. Yield state dictionaries for visualization
4. Add to `ALGORITHM_MAP` in `algorithms/views.py`
5. Update templates to include new algorithm

### Adding New Analysis Metrics

1. Update `ComplexityAnalyzer` in `analytics/complexity_analyzer.py`
2. Add metric calculation methods
3. Update `AnalysisResult` model if needed
4. Update templates to display new metrics

---

## 🤝 Contributing

This is a student project for INF601. Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Brian Shoemaker**  
Computer Science Concentration  
INF601 - Advanced Programming with Python

---

## 🙏 Acknowledgments

- Django documentation and community
- GitHub API documentation
- Algorithm visualizations inspired by VisuAlgo
- Python AST module documentation

---

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ for CS education**
