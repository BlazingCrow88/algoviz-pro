# Installation Guide

Step-by-step instructions to get AlgoViz Pro running on your machine. Should take about 10-15 minutes if everything goes smoothly.

---

## What You Need First

Make sure you have these installed before starting:
- **Python 3.9 or higher** - [Download here](https://www.python.org/downloads/) if you don't have it
- **pip** - Should come with Python automatically
- **Git** - [Download here](https://git-scm.com/downloads) if needed
- **Code Editor** - I use PyCharm but VS Code works great too

Quick check if you have Python and pip:
```bash
python --version
pip --version
```

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/algoviz-pro.git
cd algoviz-pro
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

### 2. Set Up Virtual Environment

This keeps the project dependencies separate from your system Python (trust me, this saves headaches later).

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Your terminal should now show `(venv)` at the beginning - that means it worked!

---

### 3. Install Required Packages
```bash
pip install -r requirements.txt
```

This installs:
- Django 5.1.7 (the web framework)
- requests 2.31.0 (for GitHub API calls)

Should only take a minute or two depending on your internet speed.

---

### 4. Set Up the Database
```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the SQLite database file and all the tables the app needs. You should see a bunch of "Applying..." messages - that's normal and good.

---

### 5. (Optional but Recommended) Create Admin Account

If you want to access Django's admin panel to see the database:
```bash
python manage.py createsuperuser
```

It'll ask for:
- Username (whatever you want)
- Email (can be fake for this project)
- Password (enter it twice)

You can skip this if you don't care about the admin interface.

---

### 6. Start the Server
```bash
python manage.py runserver
```

You should see something like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Leave this terminal window open - the server needs to keep running.

---

### 7. Open in Browser

Go to: **http://127.0.0.1:8000/**

If you see the AlgoViz Pro home page, you're all set! 🎉

---

## Making Sure Everything Works

### Test the Visualization
1. Click **"Visualize"** in the navbar
2. Pick an algorithm (Bubble Sort is a good start)
3. Enter some numbers: `5,2,8,1,9`
4. Hit **"Execute"**
5. Try the Play/Pause/Step buttons

If you see the bars moving around, the visualization is working!

### Test GitHub Search
1. Click **"GitHub"** in the navbar
2. Search for something like `django`
3. Pick `Python` as the language
4. Click **"Search"**

Should show you a list of repositories. First search might be slow, but then it caches the results.

### Run the Tests
```bash
python manage.py test
```

All tests should pass. If any fail, something might be configured wrong.

---

## Common Problems (and How to Fix Them)

### "ImportError: No module named 'django'"
You probably forgot to activate the virtual environment.

**Fix:**
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

Then try again.

---

### "Database is locked"
This happens if you have two terminals running the server at once.

**Fix:** Close all terminals and start fresh with just one `runserver` command.

---

### "Port already in use"
Some other app is using port 8000.

**Fix:** Run on a different port:
```bash
python manage.py runserver 8001
```

Then go to `http://127.0.0.1:8001/` instead.

---

### Static files (CSS/JS) not loading
Rarely happens but if styles look broken:

**Fix:**
```bash
python manage.py collectstatic
```

---

## Setting Up Your Editor

### PyCharm (What I Use)
1. Open the `algoviz-pro` folder in PyCharm
2. Go to Settings/Preferences → Project → Python Interpreter
3. Click the gear icon → Add → Existing Environment
4. Point it to `venv/Scripts/python.exe` (Windows) or `venv/bin/python` (Mac/Linux)
5. Right-click the `templates/` folder → Mark Directory as → Template Folder
6. Same thing for `static/` → Mark as → Resource Root
7. Enable Django: Settings → Languages & Frameworks → Django
   - Check "Enable Django Support"
   - Django project root: (should auto-detect)

PyCharm will now autocomplete Django stuff and run the server from the IDE.

### VS Code
1. Open the project folder
2. Install the Python extension (ms-python.python)
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Type "Python: Select Interpreter"
5. Choose the one that says `venv`
6. Install Django extension for better syntax highlighting

VS Code's terminal will automatically activate the venv when you open it.

---

## Next Steps

Now that it's running:

- **Check out the code** - Start with `algorithms/sorting.py` to see how the sorting algorithms work
- **Play with the visualizations** - Try different arrays and see how algorithms behave differently
- **Look at the docs** - `docs/algorithms.md` has all the complexity explanations
- **Modify something** - Change the colors in `static/css/visualization.css` or add your own algorithm

The best way to learn is to break stuff and fix it! (Just commit your working version first)

---

## If You Want to Remove Everything

To completely uninstall:
```bash
# First, deactivate the virtual environment
deactivate

# Then delete the whole project folder
cd ..
rm -rf algoviz-pro  # macOS/Linux
rmdir /s algoviz-pro  # Windows (use rmdir /s /q for no confirmation)
```

This removes everything - code, database, dependencies, all of it.

---

## Having Issues?

If something's not working, and you can't figure it out:
1. Check that your virtual environment is activated (look for `(venv)` in terminal)
2. Make sure you're in the right directory (`algoviz-pro/`)
3. Try running migrations again (`python manage.py migrate`)
4. Google the error message - Django errors are usually well-documented
5. Open an issue on GitHub if you think it's a bug in my code

Most issues are just missing a step or forgetting to activate venv. Been there many times myself!

---

**Good luck! Let me know if you run into any problems getting it set up.**