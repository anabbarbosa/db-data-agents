from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, session
from flask_cors import CORS
from data_agent.agent.controller import AgentController
from sqlalchemy import text
import random
import string
import uuid
import hashlib
import os

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="/static")
app.secret_key = os.urandom(24)
CORS(app)

def _ensure_schema_and_tables(ctrl: AgentController):
    """ensure only the question_logs table exists while the users table remains in place"""
    try:
        with ctrl.engine.connect() as conn:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS agent.question_logs (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT,
                    question TEXT NOT NULL,
                    explanation TEXT,
                    sql TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT question_logs_user_id_fkey FOREIGN KEY (user_id)
                      REFERENCES agent.users(id) ON DELETE SET NULL
                )
                """
            ))
            conn.commit()
    except Exception:
        pass

def _hash_password(password: str) -> str:
    """hash the password using sha-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def _authenticate_user(ctrl: AgentController, username: str, password: str):
    """authenticate the user and return user data"""
    try:
        with ctrl.engine.connect() as conn:
            password_hash = _hash_password(password)
            row = conn.execute(text(
                "SELECT id, username, user_group FROM agent.users WHERE username = :username AND password_hash = :pwd"
            ), {"username": username, "pwd": password_hash}).fetchone()
            if row:
                return {"id": row[0], "username": row[1], "user_group": row[2]}
    except Exception:
        pass
    return None

def _get_or_create_user(ctrl: AgentController):
    created = False
    user_key = request.cookies.get('da_user')
    provided_username = request.cookies.get('da_username') or request.args.get('username') or None

    def _gen_username(numeric_id: int) -> str:
        suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
        return f"{numeric_id}-{suffix}"
    with ctrl.engine.connect() as conn:
        if user_key:
            conn.execute(text("ALTER TABLE agent.users ADD COLUMN IF NOT EXISTS username TEXT"))
            row = conn.execute(text("SELECT id, username FROM users WHERE user_key = :uk"), {"uk": user_key}).fetchone()
            if row:
                if (row[1] is None or row[1] == ""):
                    new_username = provided_username or _gen_username(row[0])
                    conn.execute(text("UPDATE agent.users SET username = :un WHERE id = :id"), {"un": new_username, "id": row[0]})
                    conn.commit()
                return row[0], user_key, created
        user_key = str(uuid.uuid4())
        row = conn.execute(text("INSERT INTO agent.users (user_key) VALUES (:uk) RETURNING id"), {"uk": user_key}).fetchone()
        conn.commit()
        created = True
        new_username = provided_username or _gen_username(row[0])
        conn.execute(text("UPDATE agent.users SET username = :un WHERE id = :id"), {"un": new_username, "id": row[0]})
        conn.commit()
        return row[0], user_key, created

@app.route("/")
def home():    
    # check whether the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    agent = AgentController()
    _ensure_schema_and_tables(agent)
    user_id, user_key, created = _get_or_create_user(agent)
    resp = make_response(render_template("index.html"))
    if created:
        resp.set_cookie('da_user', user_key, max_age=60*60*24*365, httponly=False, samesite='Lax')
    return resp

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"success": False, "message": "username and password are required"}), 400
    
    agent = AgentController()
    _ensure_schema_and_tables(agent)
    
    user = _authenticate_user(agent, username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['user_group'] = user['user_group']
        return jsonify({"success": True, "redirect": url_for('home')})
    else:
        return jsonify({"success": False, "message": "username or password is incorrect"}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/get")
def get_bot_response():    
    # check whether the user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user_text = request.args.get("msg", "").strip()
    teaching_mode = request.args.get("teaching_mode", "0")
    
    if not user_text:
        return jsonify({
            "explanation": "please enter a question.",
            "sql": "",
            "query-explanation": "",
            "query-execution-status": "",
            "preview": {"message": "", "data": []}
        })

    agent = AgentController()
    _ensure_schema_and_tables(agent)
    
    # get the user group from the session
    user_group = session.get('user_group', 'amazon')
    result = agent.run_return(user_text, teaching_mode=int(teaching_mode), user_group=user_group)

    set_cookie_resp = None
    try:
        user_id, user_key, created = _get_or_create_user(agent)
        with agent.engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO agent.question_logs (question, explanation, sql, user_id) VALUES (:q, :e, :s, :uid)"
            ), {"q": user_text, "e": result.get("explanation", ""), "s": result.get("sql", ""), "uid": user_id})
            conn.commit()
        if created:
            set_cookie_resp = user_key
    except Exception:
        pass

    resp = make_response(jsonify(result))
    if set_cookie_resp:
        resp.set_cookie('da_user', set_cookie_resp, max_age=60*60*24*365, httponly=False, samesite='Lax')
    return resp

@app.route("/user", methods=["POST"])
def set_username():
    agent = AgentController()
    _ensure_schema_and_tables(agent)
    try:
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        if not username:
            return jsonify({"ok": False, "error": "username required"}), 400

        user_id, user_key, created = _get_or_create_user(agent)

        with agent.engine.connect() as conn:
            conn.execute(text("UPDATE agent.users SET username = :un WHERE id = :id"), {"un": username, "id": user_id})
            conn.commit()

        resp = make_response(jsonify({"ok": True}))
        resp.set_cookie('da_username', username, max_age=60*60*24*365, httponly=False, samesite='Lax')
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)