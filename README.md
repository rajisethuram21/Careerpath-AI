# CareerPath AI
Run:
1. `pip install -r requirements.txt`
2. In MySQL: `SOURCE schema.sql;`
3. Set `DB_USER`, `DB_PASSWORD` (and optionally `SECRET_KEY`), then `python app.py`
4. Open http://127.0.0.1:5000, register, then make yourself admin:
   `UPDATE students SET is_admin=1 WHERE email='you@example.com';`
Recommendation method: rule-based (see `score_careers` in app.py). No Machine Learning is used.
