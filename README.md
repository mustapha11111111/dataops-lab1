# Ventes e-commerce multi-devises

Plateforme DataOps pour suivre un chiffre d'affaires quotidien fiable, converti en euros, et signaler une journée anormale. Les commandes sont **synthétiques**. Les taux viennent de l'API Frankfurter.

## Lancer en local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m ecommerce_pipeline run --offline
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

La commande sans `--offline` appelle Frankfurter et construit l'historique du 1er septembre au 16 novembre 2026.

Avec Docker :

```powershell
docker compose up --build
```

Le tableau de bord est sur http://localhost:8501. Pour un essai sans réseau : `$env:OFFLINE = "1"` avant `docker compose up`.

## Ce que fait une exécution

1. Génère les commandes synthétiques.
2. Récupère les taux USD, TND et MAD, et ajoute le taux `1` pour l'euro.
3. Vérifie la forme des fichiers (Pandera).
4. Charge le brut dans DuckDB, sans appliquer les règles métier.
5. Lance `dbt build`. Une ligne fausse part en quarantaine. Un test rouge bloque la publication.
6. Écrit `data/alerts/latest_alert.json` et une ligne dans `ops.pipeline_runs`.

Relancer la même commande ne crée pas de nouvelle commande : les clés `order_id` et `(rate_date, base_currency, quote_currency)` sont remplacées.

## Où lire les réponses métier

Le tableau de bord ne lit que les marts, et seulement si le dernier statut est `success`.

| Question | Table |
|---|---|
| Chiffre d'affaires par jour, mois et pays, en EUR | `mart_revenue_by_country_day`, `mart_revenue_by_country_month` |
| Produits et segments | `mart_product_performance`, `mart_customer_segments` |
| Journée anormale | `mart_sales_anomalies` |

## Documents

- `docs/PROJECT_BRIEF.md` : idée à défendre
- `docs/architecture.md` : schéma et choix
- `docs/API_NOTES.md` : Frankfurter
- `docs/RUNBOOK.md` : quoi faire quand ça casse

## Règle d'équipe

Rien sur `main` sans pull request relue. La CI (`.github/workflows/ci.yml`) lance Ruff, pytest et `dbt build`. Une PR rouge ne doit pas être fusionnée.

L'ancien cahier demandait 1 million de lignes, Iceberg et AWS. Le PDF simplifié ne les impose pas. Ce dépôt livre le socle local complet. AWS viendra après, sans clé dans Git, avec une alerte de budget.
