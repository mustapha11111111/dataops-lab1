# API Frankfurter

Vérifié le 17 novembre 2026.

- URL : `https://api.frankfurter.dev/v2/rates`
- Paramètres : `from`, `to`, `base=EUR`, `quotes=USD,TND,MAD`
- Sans clé API
- Réponse : une liste d'objets `date`, `base`, `quote`, `rate`
- Sur le 1er au 12 octobre 2026, l'API a renvoyé 36 lignes, soit les trois devises pour chaque jour, week-end compris

Ce sont des taux de référence, pas un carnet d'ordres en temps réel.

Le client :

- impose un délai de 30 secondes ;
- relance deux fois sur un délai dépassé, un HTTP 429 ou un HTTP 5xx ;
- échoue tout de suite sur un HTTP 4xx ;
- refuse une réponse vide ou illisible ;
- lit les nombres en `Decimal` pour éviter un float binaire.

Le pipeline demande aussi les 7 jours avant la première commande. La conversion dbt prend le dernier taux dont la date est inférieure ou égale à la commande. Le test `test_weekend_order_uses_the_previous_rate` retire volontairement le taux du 4 octobre 2026 : la commande de ce dimanche utilise le taux du 2 octobre.

Pour l'euro, le pipeline ajoute lui-même le taux `1.000000`, source `interne_identite_eur`.

Le mode `--offline` relit `tests/fixtures/frankfurter_oct2026.json`, capturé sur l'API réelle. Il couvre du 1er au 12 octobre 2026.
