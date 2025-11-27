# AlgoViz Pro - System Architecture

This document explains how I structured AlgoViz Pro and the design decisions
I made along the way. Basically breaking down why things are organized the 
way they are.

---

## Project Overview

AlgoViz Pro is a Django web app I built to demonstrate advanced Python 
concepts for INF601. It combines algorithm visualization, GitHub API integration,
and code complexity analysis into one platform.

**Tech Stack:**
- **Backend:** Django 5.1.7 - chose this because it handles a lot of the 
boilerplate stuff
- **Database:** SQLite for dev (comes built-in), can swap to PostgresSQL 
for production
- **Frontend:** Just vanilla HTML5, CSS3, and JavaScript - no frameworks needed
- **Visualization:** HTML5 Canvas API - surprisingly powerful for drawing 
the arrays
- **Code Analysis:** Python's AST module - this was cool to work with
- **API Integration:** GitHub REST API v3

---

## Django's MTV Pattern

Django uses **Model-Template-View (MTV)** architecture, which is basically 
their version of MVC:

### **Models (Data Layer)**
- Define what the database tables look like
- Handle business logic related to data
- Examples in my project: `Algorithm`, `ExecutionLog`, `Repository`, `AnalysisResult`

### **Templates (Presentation Layer)**
- HTML files with Django's template syntax
- All mine are in the `/templates/` directory
- They inherit from `base.html` so I don't repeat navbar code everywhere

### **Views (Business Logic Layer)**
- Handle HTTP requests and responses
- Execute the actual algorithms
- Return either JSON data or rendered HTML pages
- Input validation and error handling happens here

**Why MTV works:**  
Each part does its own thing. I can change the database structure 
without touching the HTML, or update the UI without messing with algorithm code.
Makes debugging way easier.

---

## App Organization - Why 4 Apps?

I split the project into **4 separate Django apps** instead of cramming 
everything into one. Each app has a specific job:

### **1. algorithms/**
**What it does:** Core algorithm implementations and execution logic

**Main files:**
- `models.py` - Database models for algorithms and execution logs
- `sorting.py` - All the sorting algorithms (Bubble, Merge, Quick Sort)
- `searching.py` - Search algorithms (Binary, Linear, BFS)
- `views.py` - Handles HTTP requests for running algorithms
- `urls.py` - Routes URLs to the right view functions
- `tests.py` - Unit tests (these saved me a few times)

**Design Pattern I used:** **Strategy Pattern**
- Base classes: `SortingAlgorithm` and `SearchingAlgorithm`
- Each algorithm inherits from these 
and implements a `sort()` or `search()` method
- Makes it easy to add new algorithms without changing existing code
- Professor mentioned this in class and it made sense here

---

### **2. visualization/**
**What it does:** The actual web interface where users see things happen

**Main files:**
- `views.py` - Renders the visualization pages
- `urls.py` - URL routing
- Templates: `home.html` (landing page), `visualize.html` (main visualization)

**How it works:**
- JavaScript file (`visualizer.js`) handles all the Canvas drawing
- Makes AJAX calls to get algorithm steps from the backend
- Updates stats in real-time as the visualization runs

This separation kept the frontend and backend code from getting tangled up.

---

### **3. github_integration/**
**What it does:** Talks to GitHub's API to search repos and analyze code

**Main files:**
- `api_client.py` - `GitHubAPIClient` class that handles all API calls
- `models.py` - Caches repository data so we don't hammer GitHub's API
- `views.py` - Search interface and data display
- `urls.py` - URL routing

**Design Pattern:** **Repository Pattern**
- Basically abstracts away how we get the data
- The rest of the app doesn't care if data comes from GitHub, cache,
- or elsewhere
- Makes testing easier too

**Why this matters:**  
If I ever wanted to switch to GitLab or add another API, I'd only need
to change `api_client.py`. The views and templates wouldn't know the difference.


---

### **4. analytics/**
**What it does:** Analyzes Python code complexity using AST

**Main files:**
- `complexity_analyzer.py` - The `ComplexityAnalyzer` class that does the heavy lifting
- `models.py` - Stores analysis results
- `views.py` - Handles analysis requests
- `urls.py` - URL routing

**What it analyzes:**
- Cyclomatic complexity (how many decision points in the code)
- Function length and parameter count
- Nesting depth (how many levels of indentation)
- Generates a maintainability score

The AST module was fascinating to work with - 
it parses Python code into a tree structure you can traverse.

---

## How Data Flows Through The System

### **Running an Algorithm**
Here's what happens when someone clicks "Sort":
```
1. User enters array in the form
   ↓
2. Browser sends POST to /algorithms/execute/bubble/
   ↓
3. Django view checks if input is valid (size, format, etc.)
   ↓
4. Creates a BubbleSort object
   ↓
5. Calls sort() - this is a generator function
   ↓
6. Generator yields states after each comparison/swap
   Each state = {array: [...], comparisons: n, swaps: m}
   ↓
7. View collects all states into a list
   ↓
8. Returns JSON with all the steps
   ↓
9. JavaScript grabs the JSON and draws each state on Canvas
   ↓
10. User can play/pause/step through the visualization
```

Using generators for this was actually really clever (if I do say so myself)
- each `yield` pauses the algorithm and sends the current state, 
- so the frontend can show it step-by-step.

---

### **GitHub Search Flow**
```
1. User searches for repositories
   ↓
2. Check Django's cache first
   ↓
3. Found in cache? → Return it immediately
   ↓
4. Not in cache? → Make API request to GitHub
   ↓
5. Handle rate limits (GitHub allows 60 requests/hour without auth)
   ↓
6. Cache the response for 30 minutes
   ↓
7. Show results
```

Caching was essential here because GitHub's rate limit is pretty strict.
Without caching, the app would hit the limit really fast.

---

### **Code Analysis Flow**
```
1. User pastes Python code into form
   ↓
2. ComplexityAnalyzer parses it with Python's ast module
   ↓
3. Calculate various metrics:
   - Cyclomatic complexity (counts if/for/while/etc)
   - Lines of code per function
   - Maximum nesting depth
   - Maintainability index (0-100 scale)
   ↓
4. Save results to database
   ↓
5. Display formatted report with suggestions
```

---

## Caching Strategy

### **Why Cache?**
- GitHub limits unauthenticated requests to 60/hour
- Same search queries don't need fresh data every time
- Makes the app feel faster

### **How I Implemented It**
- Using Django's cache framework (built right in)
- In dev: local memory cache (simple, works great)
- For production: can switch to Redis easily
- Cache expires after 30 minutes

**Code example:**
```python
cache_key = f'github_api:search:{query}:{language}'
cached_result = cache.get(cache_key)

if cached_result:
    return cached_result  # Already have it
else:
    result = fetch_from_github()  # Go get it
    cache.set(cache_key, result, timeout=1800)  # Save for later
    return result
```

Pretty straightforward, but it makes a huge difference in API usage.

---

## Error Handling

I tried to handle errors at multiple levels so users get helpful messages
instead of crashes:

**1. Input Validation (Views)**
- Check array size, format, data types before processing
- Return clear error messages like "Array too large (max 100 elements)"
- Better to catch bad input early

**2. API Errors (GitHub Client)**
- Handle network timeouts and connection failures
- Catch rate limit errors and show when limits reset
- Handle 404s when repos don't exist
- Custom exception classes like `RateLimitError` make this cleaner

**3. Code Parsing Errors (Analytics)**
- Catch Python syntax errors in submitted code
- Show the error with line number
- Example: "SyntaxError: invalid syntax (line 5)"

**4. User-Friendly Messages**
- Never show those ugly Python tracebacks to users
- Give actionable advice
- Example: "Rate limit reached. Try again in 45 minutes or add 
GitHub authentication for higher limits."

The goal was making sure users know what went wrong and what they 
can do about it.

---

## Database Design

### **algorithms_algorithm table**
```sql
- id (Primary Key)
- name (up to 100 chars)
- category (SORT, SEARCH, or GRAPH)
- description (text field)
- time_complexity_best/average/worst (complexity strings)
- space_complexity (complexity string)
- is_stable (true/false for sorting algorithms)
- created_at (timestamp)
```

### **algorithms_execution table**
```sql
- id (Primary Key)
- algorithm_id (Foreign Key to algorithms_algorithm)
- input_size (how many elements)
- execution_time_ms (float - milliseconds)
- comparisons (count)
- swaps (count)
- executed_at (timestamp)

Indexes on: (algorithm_id, input_size) and (executed_at)
```

These indexes make queries way faster when looking up execution history.

### **github_integration_repository table**
```sql
- id (Primary Key)
- full_name (unique, like "owner/repo")
- owner (username)
- name (repo name)
- description (text)
- html_url (link to GitHub)
- stargazers_count (stars)
- forks_count (forks)
- language (primary language)
- cached_at (when we fetched this)

Indexes on: (owner, name) and (language)
```

The cached_at field helps me know when to refresh stale data.

---

## Design Patterns I Used

These are some patterns I learned in class that actually made sense
to use here:

1. **Strategy Pattern** (Algorithms app)
   - Different algorithms, same interface
   - Can swap them out without breaking anything
   - Example: All sorting algorithms have a `sort(array)` method

2. **Repository Pattern** (GitHub integration)
   - Hides how we get data (API, cache, database)
   - Makes testing way easier
   - Could swap GitHub for GitLab without changing views

3. **Generator Pattern** (Algorithm execution)
   - Yields states one at a time instead of building huge list
   - Memory efficient
   - Perfect for step-by-step visualization

4. **Singleton-ish Pattern** (API Client)
   - One shared session for all HTTP requests
   - Connection pooling = faster requests

I tried not to over-engineer things with patterns just for the sake of it,
but these actually solved real problems I had.

---

## Security Stuff

Django handles a lot of security out of the box, but here's what I made
sure was covered:

- **CSRF Protection:** Django's middleware handles this automatically
- **SQL Injection:** Using Django's ORM means I never write raw SQL
- **XSS Prevention:** Templates auto-escape variables (no malicious scripts)
- **Rate Limiting:** Respecting GitHub's API limits
- **Input Validation:** Sanitizing everything users submit

Basically following Django best practices keeps most security issues away.

---

## Performance Optimizations

Things I did to make the app faster:

1. **Caching** - Reduces API calls and repeated database queries
2. **Database Indexes** - Fast lookups on commonly queried fields
3. **Generator Functions** - Don't load entire algorithm execution
into memory at once
4. **AJAX** - Load data asynchronously so pages don't freeze
5. **Static Files** - CSS/JS served efficiently (ready for CDN in production)

Most of these weren't premature optimization - I added them when 
I noticed actual slowness.

---

## What I'd Add If I Had More Time

- **User Authentication** - Let people save favorite algorithms and 
execution history
- **Redis Caching** - More robust than memory cache for production
- **WebSockets** - Real-time collaboration on algorithm visualization
- **More Algorithms** - Heap Sort, Radix Sort, Dijkstra's, A*
- **Side-by-Side Comparison** - Run two algorithms simultaneously
- **Mobile Responsive** - Touch controls and better mobile layout

Some of these would be cool features, others are more "production-ready"
concerns.

---

## Production Deployment Architecture

If this was going to production, here's how I'd set it up:
```
                   ┌─────────────┐
                   │   Nginx     │  Web server (handles static files)
                   └──────┬──────┘
                          │
                   ┌──────┴──────┐
                   │  Gunicorn   │  WSGI server (runs Django)
                   └──────┬──────┘
                          │
                   ┌──────┴──────┐
                   │   Django    │  Application layer
                   └──────┬──────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    ┌─────┴─────┐   ┌────┴────┐   ┌─────┴─────┐
    │PostgreSQL │   │  Redis  │   │  GitHub   │
    │ (Database)│   │ (Cache) │   │   (API)   │
    └───────────┘   └─────────┘   └───────────┘
```

Right now it's just Django's dev server with SQLite, which is fine
for the project but wouldn't scale.

---

## Final Thoughts

This architecture evolved as I built the project - didn't plan 
everything perfectly upfront. Started with one big app, then 
refactored into four as things got messy. The modular structure
made adding new features way easier than I expected.

The biggest win was using generators for algorithm execution - 
that made the step-by-step visualization possible without crazy memory usage.
Second biggest was the caching strategy, which kept me from hitting rate
limits constantly during testing.

Overall, trying to follow good architecture principles 
(separation of concerns, DRY, etc.) made the codebase way more maintainable
than my previous projects. Definitely took more time upfront but saved time
in the long run.