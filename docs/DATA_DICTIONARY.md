# Dictionnaire des commandes

Fichier d'exemple : `data/samples/orders_sample.csv`. Il est produit par le générateur du projet, pas par une extraction de clients réels. La colonne `data_origin` vaut toujours `synthetique`.

| Colonne | Sens | Exemple |
|---|---|---|
| order_id | Identifiant stable de la commande. Clé d'idempotence. | 20261001001 |
| order_date | Jour de la commande, texte `AAAA-MM-JJ` dans le brut | 2026-10-01 |
| customer_id | Client. Peut être vide : la ligne reste publiée, sans segment. | C001 |
| country | Pays tel que reçu. Le staging corrige `tunisia` en `Tunisia`. | France |
| product | Produit du catalogue de la boutique | Mouse |
| quantity | Quantité en texte dans le brut. Une valeur négative part en quarantaine. | 1 |
| unit_price | Prix unitaire dans la devise de la commande, pas en euros | 19.90 |
| currency | EUR, USD, TND ou MAD. Toute autre valeur est rejetée. | TND |
| data_origin | Marque les lignes générées | synthetique |

Le prix catalogue en devise locale n'est pas le taux de change. La conversion en euros utilise Frankfurter : on divise le montant local par le taux, ou par 1 si la devise est l'euro.
