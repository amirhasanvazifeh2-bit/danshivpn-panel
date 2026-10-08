import base64, secrets, sqlite3, uuid
from datetime import datetime, timezone
from urllib.parse import urlencode, quote
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

DB = "danshi.db"
app = FastAPI(title="DANSHI Panel")
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))
templates = Jinja2Templates(directory="templates")

# Change these before exposing the panel publicly.
ADMIN_USER = "admin"
ADMIN_PASS = "change-me-now"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        uuid TEXT NOT NULL UNIQUE,
        server TEXT NOT NULL,
        port INTEGER NOT NULL,
        network TEXT NOT NULL DEFAULT 'ws',
        security TEXT NOT NULL DEFAULT 'tls',
        host TEXT DEFAULT '',
        path TEXT DEFAULT '/ws',
        sni TEXT DEFAULT '',
        volume_gb INTEGER DEFAULT 0,
        days INTEGER DEFAULT 30,
        users INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        expires_at TEXT
    )""")
    c.commit()
    c.close()

def logged(request):
    return request.session.get("user") == ADMIN_USER

def vless_uri(r):
    params = {
        "type": r["network"],
        "security": r["security"],
        "encryption": "none",
    }
    if r["network"] == "ws":
        params["host"] = r["host"]
        params["path"] = r["path"]
    if r["security"] == "tls":
        params["sni"] = r["sni"] or r["host"]
    query = urlencode(params, quote_via=quote)
    return f"vless://{r['uuid']}@{r['server']}:{r['port']}?{query}#{quote(r['name'])}"

init_db()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if not logged(request):
        return RedirectResponse("/login", 303)
    c = db()
    rows = c.execute("SELECT * FROM configs ORDER BY id DESC").fetchall()
    c.close()
    return templates.TemplateResponse("index.html", {"request": request, "configs": rows})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "نام کاربری یا رمز عبور اشتباه است."})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 303)

@app.post("/configs")
def create_config(
    request: Request,
    name: str = Form(...),
    country: str = Form(...),
    server: str = Form(...),
    port: int = Form(443),
    host: str = Form(""),
    path: str = Form("/ws"),
    sni: str = Form(""),
    volume_gb: int = Form(10),
    days: int = Form(30),
    users: int = Form(1),
):
    if not logged(request):
        return RedirectResponse("/login", 303)
    uid = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    # Simple expiry calculation without external packages.
    from datetime import timedelta
    expires = now + timedelta(days=max(0, days))
    c = db()
    c.execute("""INSERT INTO configs
        (name,country,uuid,server,port,host,path,sni,volume_gb,days,users,created_at,expires_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (name,country,uid,server,port,host,path,sni,volume_gb,days,users,
         now.isoformat(),expires.isoformat()))
    c.commit()
    c.close()
    return RedirectResponse("/", 303)

@app.get("/configs/{cid}/link")
def get_link(request: Request, cid: int):
    if not logged(request):
        return RedirectResponse("/login", 303)
    c = db()
    r = c.execute("SELECT * FROM configs WHERE id=?", (cid,)).fetchone()
    c.close()
    if not r:
        return HTMLResponse("Not found", 404)
    return HTMLResponse(vless_uri(r), media_type="text/plain")

@app.post("/configs/{cid}/delete")
def delete_config(request: Request, cid: int):
    if not logged(request):
        return RedirectResponse("/login", 303)
    c = db()
    c.execute("DELETE FROM configs WHERE id=?", (cid,))
    c.commit()
    c.close()
    return RedirectResponse("/", 303)
