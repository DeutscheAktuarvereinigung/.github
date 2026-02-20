import requests
import pandas as pd
import os
import datetime

# 1. Konfiguration
ORG_NAME = "DeutscheAktuarvereinigung"
today = datetime.datetime.now().date()

# Dateiname für das lokale Verzeichnis (GitHub Action Runner)
OUTPUT_CSV_PATH = f"github_traffic_dav_{today}.csv"

# 2. GitHub Token aus Umgebungsvariable lesen
# Setzt voraus, dass das Secret in GitHub Actions als PAT_TOKEN übergeben wird
GITHUB_TOKEN = os.environ.get("PAT_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("FEHLER: PAT_TOKEN Umgebungsvariable wurde nicht gefunden.")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 3. Alle Repositories der Organisation abfragen
def get_repos(org_name):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?per_page=100&page={page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Fehler beim Abrufen der Repos: {response.json().get('message')}")
            break

        data = response.json()
        if not data:
            break
        repos.extend([repo['name'] for repo in data])
        page += 1
    return repos

print(f"Lade Repositories für Organisation: {ORG_NAME}...")
repos = get_repos(ORG_NAME)
print(f"{len(repos)} Repositories gefunden. Lade Traffic-Daten...")

# 4. Traffic Daten abfragen (Views & Clones der letzten 14 Tage)
all_data = []

for repo in repos:
    print(f"Lade Traffic-Daten für Repository: {repo} ...")

    daily_stats = {}

    # Views abrufen
    views_url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/traffic/views"
    v_resp = requests.get(views_url, headers=headers)
    if v_resp.status_code == 200:
        for view in v_resp.json().get('views', []):
            date = view['timestamp'][:10]
            if date not in daily_stats:
                daily_stats[date] = {"Views": 0, "Unique Views": 0, "Clones": 0, "Unique Clones": 0}
            daily_stats[date]["Views"] = view['count']
            daily_stats[date]["Unique Views"] = view['uniques']

    # Clones abrufen
    clones_url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/traffic/clones"
    c_resp = requests.get(clones_url, headers=headers)
    if c_resp.status_code == 200:
        for clone in c_resp.json().get('clones', []):
            date = clone['timestamp'][:10]
            if date not in daily_stats:
                daily_stats[date] = {"Views": 0, "Unique Views": 0, "Clones": 0, "Unique Clones": 0}
            daily_stats[date]["Clones"] = clone['count']
            daily_stats[date]["Unique Clones"] = clone['uniques']

    for date, stats in daily_stats.items():
        all_data.append({
            "Repository": repo,
            "Datum": date,
            "Views": stats["Views"],
            "Clones": stats["Clones"],
            "Unique Views": stats["Unique Views"],
            "Unique Clones": stats["Unique Clones"]
        })

# 5. Als CSV verarbeiten und lokal speichern
df = pd.DataFrame(all_data)

if not df.empty:
    df = df[["Repository", "Datum", "Views", "Clones", "Unique Views", "Unique Clones"]]
    df = df.sort_values(by=["Repository", "Datum"], ascending=[True, False])
    
    df.to_csv(OUTPUT_CSV_PATH, index=False, sep=";")
    print("\n--- FERTIG ---")
    print(f"Daten erfolgreich gespeichert unter: {OUTPUT_CSV_PATH}")
else:
    print("\nKeine Traffic-Daten in den letzten 14 Tagen für diese Repositories gefunden.")
