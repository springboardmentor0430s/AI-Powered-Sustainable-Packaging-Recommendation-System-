from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

VALID_EMAIL = "mishrayashashree@gmail.com"
VALID_PASSWORD = "Yashu@123"


# LOGIN PAGE (GET + POST)
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == VALID_EMAIL and password == VALID_PASSWORD:
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)


# REGISTER PAGE (ONLY UI)
@app.route("/register")
def register():
    return render_template("register.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# IMPACT (BI DASHBOARD)
@app.route("/impact")
def impact():
    return render_template("impact.html")


# HISTORY
@app.route("/history")
def history():
    return render_template("history.html")


if __name__ == "__main__":
    app.run(debug=True)