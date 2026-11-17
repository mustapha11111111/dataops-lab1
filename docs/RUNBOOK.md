# Runbook

## Exécution normale

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m ecommerce_pipeline run
```

Résultat attendu : statut `success`, fichier `data/alerts/latest_alert.json`, tables `raw.orders` et `raw.exchange_rates`, marts interrogeables.

## Deuxième passage

Relancer la même commande. `orders_in_raw` et le nombre de `order_id` distincts restent les mêmes. `_loaded_at` change.

## API en panne

Le programme affiche l'erreur HTTP ou le délai, écrit une alerte `critical`, et quitte avec le code 1. Les marts précédents ne sont pas présentés par le tableau de bord, car le dernier statut n'est plus `success`.

Pour préparer la soutenance sans réseau :

```powershell
.\.venv\Scripts\python.exe -m ecommerce_pipeline run --offline
```

## Ligne fausse

Elle reste dans `raw.orders` et dans `int_orders_rejected`, avec `rejection_reason`. Elle n'est pas dans `fct_sales`. Si plus de 20 % des lignes sont rejetées, `dbt build` échoue.

## Alerte métier

Un pic au-dessus de 2,5 fois la médiane du pays produit `alert_level = warning` et le statut reste `success` : la donnée est valide, mais un humain doit regarder la journée. Le pic tunisien du générateur sert à montrer ce cas.

## Scheduler

```powershell
.\.venv\Scripts\python.exe -m ecommerce_pipeline schedule
```

Le process attend 06:00, heure locale, puis lance le flow Prefect `ventes-quotidiennes`. La tâche a deux relances en cas d'échec.

## Reconstruire

Supprimer `data/warehouse.duckdb`, puis relancer. Ne pas committer ce fichier, ni un fichier `.env`.
