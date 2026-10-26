import os
from functools import wraps
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
SKILLS = ["Python", "Java", "SQL", "HTML/CSS", "JavaScript", "Flask",
          "Statistics", "Communication", "Problem Solving"]
GAP_LIMIT = 3  # a skill rated below this counts as a gap


def db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"), user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""), database=os.environ.get("DB_NAME", "careerpath"))


def query(sql, args=(), one=False, write=False):
    con = db(); cur = con.cursor(dictionary=True)
    cur.execute(sql, args)
    result = None
    if write:
        con.commit(); result = cur.lastrowid
    else:
        result = cur.fetchone() if one else cur.fetchall()
    cur.close(); con.close()
    return result


def login_required(admin=False):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            if "sid" not in session:
                return redirect(url_for("login"))
            if admin and not session.get("admin"):
                flash("Admin access only.", "error")
                return redirect(url_for("assessment"))
            return f(*a, **k)
        return wrapper
    return deco


def score_careers(levels):
    """Match score = average of (rating / 5) over a career's required skills; unrated = 0."""
    results = []
    for c in query("SELECT * FROM careers"):
        req = [s.strip() for s in c["required_skills"].split(",") if s.strip()]
        pct = sum(levels.get(s, 0) / 5 for s in req) / len(req) * 100
        gaps = [s for s in req if levels.get(s, 0) < GAP_LIMIT]
        results.append({**c, "score": round(pct, 2), "req": req, "gaps": gaps})
    return sorted(results, key=lambda r: r["score"], reverse=True)


@app.route("/")
def home():
    return redirect(url_for("assessment" if "sid" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        if len(f["password"]) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif query("SELECT 1 FROM students WHERE email=%s", (f["email"],), one=True):
            flash("That email is already registered. Log in instead.", "error")
        else:
            query("INSERT INTO students (name,email,password_hash,degree) VALUES (%s,%s,%s,%s)",
                  (f["name"], f["email"], generate_password_hash(f["password"]), f["degree"]), write=True)
            flash("Account created. Log in to continue.", "ok")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        s = query("SELECT * FROM students WHERE email=%s", (request.form["email"],), one=True)
        if s and check_password_hash(s["password_hash"], request.form["password"]):
            session.update(sid=s["student_id"], name=s["name"], admin=bool(s["is_admin"]))
            return redirect(url_for("assessment"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
@login_required()
def profile():
    if request.method == "POST":
        query("UPDATE students SET name=%s, degree=%s WHERE student_id=%s",
              (request.form["name"], request.form["degree"], session["sid"]), write=True)
        session["name"] = request.form["name"]
        flash("Profile saved.", "ok")
    s = query("SELECT * FROM students WHERE student_id=%s", (session["sid"],), one=True)
    return render_template("profile.html", s=s)


@app.route("/assessment", methods=["GET", "POST"])
@login_required()
def assessment():
    if request.method == "POST":
        for sk in SKILLS:
            lvl = int(request.form.get(sk, 0))
            query("INSERT INTO student_skills (student_id,skill_name,skill_level) VALUES (%s,%s,%s) "
                  "ON DUPLICATE KEY UPDATE skill_level=%s", (session["sid"], sk, lvl, lvl), write=True)
        return redirect(url_for("results"))
    saved = {r["skill_name"]: r["skill_level"] for r in
             query("SELECT * FROM student_skills WHERE student_id=%s", (session["sid"],))}
    return render_template("assessment.html", skills=SKILLS, saved=saved)


@app.route("/results")
@login_required()
def results():
    levels = {r["skill_name"]: r["skill_level"] for r in
              query("SELECT * FROM student_skills WHERE student_id=%s", (session["sid"],))}
    if not levels:
        return redirect(url_for("assessment"))
    ranked = score_careers(levels)
    query("DELETE FROM recommendations WHERE student_id=%s", (session["sid"],), write=True)
    for r in ranked:
        query("INSERT INTO recommendations (student_id,career_id,match_score) VALUES (%s,%s,%s)",
              (session["sid"], r["career_id"], r["score"]), write=True)
        r["courses"] = [c for g in r["gaps"] for c in
                        query("SELECT * FROM courses WHERE skill_name=%s", (g,))]
    return render_template("results.html", ranked=ranked, levels=levels)


@app.route("/admin", methods=["GET", "POST"])
@login_required(admin=True)
def admin():
    f = request.form
    if request.method == "POST":
        if f["kind"] == "career":
            query("INSERT INTO careers (career_name,description,required_skills) VALUES (%s,%s,%s)",
                  (f["career_name"], f["description"], f["required_skills"]), write=True)
        elif f["kind"] == "course":
            query("INSERT INTO courses (course_name,skill_name,course_url) VALUES (%s,%s,%s)",
                  (f["course_name"], f["skill_name"], f["course_url"]), write=True)
        elif f["kind"] == "delete_career":
            query("DELETE FROM careers WHERE career_id=%s", (f["id"],), write=True)
        elif f["kind"] == "delete_course":
            query("DELETE FROM courses WHERE course_id=%s", (f["id"],), write=True)
        flash("Saved.", "ok")
        return redirect(url_for("admin"))
    return render_template(
        "admin.html",
        students=query("SELECT student_id,name,email,degree FROM students WHERE is_admin=0"),
        careers=query("SELECT * FROM careers"), courses=query("SELECT * FROM courses"),
        reports=query("SELECT c.career_name, COUNT(*) n, ROUND(AVG(r.match_score),1) avg_score "
                      "FROM recommendations r JOIN careers c USING(career_id) GROUP BY c.career_id"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
