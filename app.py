from flask import Flask, request, render_template_string
import duckdb
from datetime import datetime

app = Flask(__name__)

def init_db():
    con = duckdb.connect("texte.db")
    # Existierende Tabelle löschen (damit immer ein sauberes Schema!)
    con.execute("DROP TABLE IF EXISTS eingaben")
    # Neu anlegen: original + reversed + timestamp als TEXT
    con.execute("""
        CREATE TABLE eingaben (
          original TEXT,
          reversed TEXT,
          ts       TEXT
        )
    """)
    con.close()

init_db()

HTML = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Text-Umkehrer</title>
  <style>
    textarea { width:300px; height:100px; }
    table { border-collapse: collapse; margin-top:20px; }
    td, th { border:1px solid #666; padding:4px 8px; }
  </style>
</head>
<body>
  <h1>Text-Umkehrer</h1>
  <form method="post">
    <p>Gib beliebige Text-Zeilen ein (jede in einer neuen Zeile):</p>
    <textarea name="text_input" placeholder="Hallo Welt\nPython">&nbsp;{{ text_input }}</textarea><br>
    <button type="submit">Umkehren &amp; Speichern</button>
  </form>

  {% if results %}
    <h2>Neu umgekehrt</h2>
    <ul>
      {% for orig, rev in results %}
        <li><strong>{{ orig }}</strong> → {{ rev }}</li>
      {% endfor %}
    </ul>
  {% endif %}

  <h2>Historie</h2>
  <table>
    <tr><th>#</th><th>Original</th><th>Reversed</th><th>Zeit</th></tr>
    {% for idx, orig, rev, ts in history %}
    <tr>
      <td>{{ idx }}</td>
      <td>{{ orig }}</td>
      <td>{{ rev }}</td>
      <td>{{ ts }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""

def reverse_text_line(s: str) -> str:
    # Dreht die Zeichen in s um
    return s[::-1]

@app.route("/", methods=["GET", "POST"])
def index():
    text_input = ""
    results = []

    # Verbindung öffnen
    con = duckdb.connect("texte.db")

    if request.method == "POST":
        # den kompletten Text aus dem <textarea>
        text_input = request.form.get("text_input", "")
        # in Zeilen aufsplitten
        lines = [zeile for zeile in text_input.splitlines() if zeile.strip() != ""]
        for line in lines:
            rev = reverse_text_line(line)
            results.append((line, rev))
            # Parametrisierte Query verhindert SQL-Injection
            ts = datetime.now().isoformat(sep=" ", timespec="seconds")
            con.execute(
                "INSERT INTO eingaben (original, reversed, ts) VALUES (?, ?, ?)",
                [line, rev, ts]
            )

    # Alle bisherigen Einträge laden
    raw = con.execute(
      "SELECT original, reversed, ts FROM eingaben ORDER BY ts DESC"
    ).fetchall()
    con.close()

    # Nummerierung in Python per enumerate
    history = [
        (i+1, orig, rev, ts)
        for i, (orig, rev, ts) in enumerate(raw)
    ]

    return render_template_string(
        HTML,
        text_input=text_input,
        results=results,
        history=history
    )

if __name__ == "__main__":
    app.run(debug=True)
