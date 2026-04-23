import sys

with open('backend/main.py', 'r') as f:
    content = f.read()

# Add imports
imports_to_add = """
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
"""
content = content.replace('from fastapi import FastAPI', 'from fastapi import FastAPI\n' + imports_to_add)

# Mount static files and templates
mount_code = """
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
"""
content = content.replace('app = FastAPI(title="UM CRM API", version="1.0.0", lifespan=lifespan)', 'app = FastAPI(title="UM CRM API", version="1.0.0", lifespan=lifespan)\n' + mount_code)

# Add /login route
login_route = """
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
"""
content = content + '\n' + login_route

with open('backend/main.py', 'w') as f:
    f.write(content)
