import os
import uuid
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# কনফিগারেশন
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///secure_layouts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ডাটাবেজ মডেল
class LandingPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(50), unique=True, nullable=False)
    layout_name = db.Column(db.String(100), nullable=False)
    tracking_url = db.Column(db.Text, nullable=False)
    ad_code = db.Column(db.Text, nullable=True)
    base_html = db.Column(db.Text, nullable=False)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin12345")

with app.app_context():
    db.create_all()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---- HTML টেমপ্লেটসমূহ (ইনলাইন) ----
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"></head>
<body class="bg-light d-flex align-items-center" style="height: 100vh;">
    <div class="container" style="max-width: 400px;"><div class="card shadow"><div class="card-body">
    <h4 class="text-center mb-4">প্যানেল লগইন</h4>
    <form method="POST">
        <div class="mb-3"><label>ইউজারনেম</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label>পাসওয়ার্ড</label><input type="password" name="password" class="form-control" required></div>
        <button type="submit" class="btn btn-primary w-100">প্রবেশ করুন</button>
    </form>
    </div></div></div>
</body>
</html>
"""

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Dashboard</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"></head>
<body class="bg-light"><div class="container my-5" style="max-width: 800px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>লেআউট ও কোড ম্যানেজার</h2>
        <div><a href="/pages" class="btn btn-info btn-sm">সব পেজ</a> <a href="/logout" class="btn btn-danger btn-sm">লগআউট</a></div>
    </div>
    <div class="card shadow"><div class="card-body">
        <form method="POST">
            <div class="mb-3"><label>লেআউট নাম</label><input type="text" name="layout_name" class="form-control" required></div>
            <div class="mb-3"><label>টার্গেট ট্র্যাকিং লিংক</label><input type="url" name="tracking_url" class="form-control" required></div>
            <div class="mb-3"><label>অ্যাড নেটওয়ার্ক স্ক্রিপ্ট (Optional)</label><textarea name="ad_code" class="form-control" rows="2"></textarea></div>
            <div class="mb-3"><label>মূল এইচটিএমএল কোড</label><textarea name="base_html" class="form-control" rows="8" required></textarea></div>
            <button type="submit" class="btn btn-success w-100">পেজ তৈরি করুন</button>
        </form>
    </div></div>
</div></body>
</html>
"""

PAGES_LIST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Pages</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"></head>
<body class="bg-light"><div class="container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4"><h2>লাইভ পেজসমূহ</h2><a href="/dashboard" class="btn btn-primary">নতুন পেজ</a></div>
    <div class="card shadow"><div class="card-body"><table class="table table-striped">
        <thead><tr><th>নাম</th><th>আইডি</th><th>লিংক</th><th>অ্যাকশন</th></tr></thead>
        <tbody>
            {% for page in pages %}
            <tr><td>{{ page.layout_name }}</td><td><code>{{ page.page_id }}</code></td>
            <td><a href="/page/{{ page.page_id }}" target="_blank">ভিজিট লিংক</a></td>
            <td><a href="/delete/{{ page.id }}" class="btn btn-danger btn-sm" onclick="return confirm('ডিলিট?')">ডিলিট</a></td></tr>
            {% endfor %}
        </tbody>
    </table></div></div>
</div></body>
</html>
"""

VIEW_PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{{ layout_name }}</title>
    {{ ad_code | safe }}
</head>
<body>
    {{ base_html | safe }}
</body>
</html>
"""

# ---- রাউটিং ----
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        layout_name = request.form.get('layout_name')
        tracking_url = request.form.get('tracking_url')
        ad_code = request.form.get('ad_code')
        base_html = request.form.get('base_html')
        
        unique_id = str(uuid.uuid4())[:8]
        new_page = LandingPage(page_id=unique_id, layout_name=layout_name, tracking_url=tracking_url, ad_code=ad_code, base_html=base_html)
        db.session.add(new_page)
        db.session.commit()
        return redirect(url_for('pages_list'))
    return render_template_string(INDEX_HTML)

@app.route('/pages')
@login_required
def pages_list():
    pages = LandingPage.query.all()
    return render_template_string(PAGES_LIST_HTML, pages=pages)

@app.route('/page/<page_id>')
def view_page(page_id):
    page = LandingPage.query.filter_by(page_id=page_id).first_or_404()
    final_html = page.base_html.replace('{{TRACKING_URL}}', page.tracking_url)
    if page.ad_code:
        final_html = VIEW_PAGE_HTML.replace('{{ ad_code | safe }}', page.ad_code).replace('{{ base_html | safe }}', final_html)
    else:
        final_html = VIEW_PAGE_HTML.replace('{{ ad_code | safe }}', '').replace('{{ base_html | safe }}', final_html)
    return render_template_string(final_html, layout_name=page.layout_name)

@app.route('/delete/<int:id>')
@login_required
def delete_page(id):
    page = LandingPage.query.get_or_404(id)
    db.session.delete(page)
    db.session.commit()
    return redirect(url_for('pages_list'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
