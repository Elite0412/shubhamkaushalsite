from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "notes.db"
ADMIN_PASSWORD = "ShubhamKaushal01010101"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-on-vercel")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def init_db() -> None:
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.commit()


@app.before_request
def setup() -> None:
    init_db()


@app.teardown_appcontext
def close_db(_: object | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/notes")
def notes():
    rows = get_db().execute(
        "SELECT id, title, description, updated_at FROM notes ORDER BY id DESC"
    ).fetchall()
    return render_template("notes.html", notes=rows)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password", "") == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Welcome, admin!", "success")
            return redirect(url_for("admin_panel"))
        flash("Incorrect password", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("home"))


def is_admin() -> bool:
    return bool(session.get("is_admin"))


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not is_admin():
        flash("Please login to continue", "error")
        return redirect(url_for("admin_login"))

    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not description:
            flash("Title and description are required", "error")
        else:
            now = datetime.now(timezone.utc).isoformat()
            db.execute(
                "INSERT INTO notes (title, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, description, now, now),
            )
            db.commit()
            flash("Note added", "success")
            return redirect(url_for("admin_panel"))

    rows = db.execute("SELECT id, title, description FROM notes ORDER BY id DESC").fetchall()
    return render_template("admin_panel.html", notes=rows)


@app.route("/admin/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id: int):
    if not is_admin():
        flash("Please login to continue", "error")
        return redirect(url_for("admin_login"))

    db = get_db()
    note = db.execute(
        "SELECT id, title, description FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    if note is None:
        flash("Note not found", "error")
        return redirect(url_for("admin_panel"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not description:
            flash("Title and description are required", "error")
        else:
            now = datetime.now(timezone.utc).isoformat()
            db.execute(
                "UPDATE notes SET title = ?, description = ?, updated_at = ? WHERE id = ?",
                (title, description, now, note_id),
            )
            db.commit()
            flash("Note updated", "success")
            return redirect(url_for("admin_panel"))

    return render_template("edit_note.html", note=note)


@app.route("/admin/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id: int):
    if not is_admin():
        flash("Please login to continue", "error")
        return redirect(url_for("admin_login"))

    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    flash("Note deleted", "success")
    return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    app.run(debug=True)
