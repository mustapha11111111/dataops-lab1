# Compte rendu — TP2 : Versionner le code avec Git et les données avec DVC

## TP2

### Objectif

L'objectif de ce TP est de versionner le code avec Git et les données avec DVC afin de pouvoir retrouver les versions précédentes du pipeline et reproduire les résultats obtenus.

### Q1. Pendant que vous travailliez sur la branche, main contenait-elle la règle 6 ? À quelle commande est-elle apparue sur main ? Pourquoi est-ce utile si le rapport tourne chaque nuit depuis main ?

Non, la branche principale ne contenait pas la règle 6 pendant le développement sur `feature/country-rule`. La règle est apparue sur `master` après la commande `git merge --no-ff feature/country-rule -m "Merge the country rule"`.

Cela permet de développer et de tester une modification séparément avant de l'intégrer au code principal. On limite ainsi le risque de perturber le rapport exécuté chaque nuit.

### Q2. Dans une vraie équipe, que permettrait une pull request qu'un git merge local n'apporte pas ?

Une pull request permet aux autres membres de l'équipe de consulter les modifications, de commenter le code, de vérifier les tests automatiques et de détecter d'éventuelles erreurs avant la fusion. Elle facilite la collaboration et la validation des changements.

### Q3. Que représente la ligne md5 de data/raw.dvc ? Que se passerait-il si un caractère d'un CSV changeait ?

Pour la version `data-v1`, la ligne est :

```yaml
- md5: 5e2dfe8f264bf13e171c4610315ced04.dir
```

Cette empreinte identifie le contenu du dossier de données suivi par DVC. Si un caractère d'un CSV change, l'empreinte du contenu concerné change également. DVC peut ainsi détecter que les données ont été modifiées et enregistrer une nouvelle version.

### Q4. Quel fichier permet à Git d'ignorer les CSV ?

Le fichier `data/.gitignore` contient la règle `/raw`, qui indique à Git d'ignorer le dossier `data/raw`. Les données restent présentes sur le disque, mais leur versionnement est géré par DVC.

### Q5. Comment les fichiers du remote DVC sont-ils nommés et pourquoi est-ce utile ?

Les objets sont stockés selon leur empreinte de contenu, notamment avec des noms basés sur MD5. Cette organisation permet à DVC d'identifier les contenus, de détecter les modifications et de réutiliser les objets identiques entre plusieurs versions au lieu de stocker inutilement plusieurs copies.

### Q6. Pourquoi deux lignes modifiées dans data/raw.dvc suffisent-elles ? Pourquoi faut-il commiter ?

Le fichier `data/raw.dvc` contient un pointeur vers les données, notamment leur empreinte et leur taille. Lorsque les données changent, Git n'a donc besoin d'enregistrer que les modifications de ce petit fichier, plutôt que le contenu complet des CSV.

Il faut commiter le pointeur pour conserver dans l'historique Git la référence exacte à la version des données utilisée.

### Q7. Entre data-v1 et data-v2, le code a-t-il changé ? Quels sont les deux totaux ?

Non, le code du pipeline n'a pas changé entre ces deux versions. Ce sont les données qui ont changé : cinq nouvelles commandes ont été ajoutées.

- `data-v1` : total de **7655.90**.
- `data-v2` : total de **8835.40**.

### Q8. Que changent git checkout data-v1 -- data/raw.dvc et dvc checkout ?

La commande `git checkout data-v1 -- data/raw.dvc` restaure dans l'espace de travail le fichier pointeur correspondant à `data-v1`.

La commande `dvc checkout` utilise ce pointeur pour restaurer les données correspondantes dans le dossier `data/raw`.

### Q9. Que se passe-t-il si l'on oublie dvc checkout ? Pourquoi est-ce dangereux ?

Le pointeur Git peut correspondre à une ancienne version alors que les fichiers présents sur le disque correspondent encore à la version récente. Le pipeline risque alors de produire un résultat qui ne correspond pas à la version de données sélectionnée.

C'est dangereux pour un rapport, car on pourrait présenter un chiffre sans pouvoir garantir qu'il provient des données attendues.

### Q10. Qu'est-ce que git clone donne au collègue et qu'est-ce que dvc pull lui donne ?

`git clone` récupère le dépôt Git, notamment le code source, l'historique des commits, les tags et les fichiers pointeurs de DVC.

`dvc pull` récupère depuis le remote DVC les données correspondant aux pointeurs du dépôt. Le collègue peut alors exécuter le pipeline avec les mêmes données et obtenir le même total, soit **8835.40**.

### Q11. Que se passerait-il si dvc push avait été oublié à l'étape 4 ?

Le pointeur `data/raw.dvc` de `data-v2` serait présent dans Git, mais les nouveaux objets de données pourraient être absents du remote DVC. Un collègue qui clone le dépôt puis exécute `dvc pull` ne pourrait pas récupérer correctement cette version et pourrait obtenir une erreur de données manquantes.

Il ne faut donc pas supposer qu'il obtiendrait automatiquement le total de `data-v2`. Il faut pousser les données avec `dvc push` pour rendre la nouvelle version disponible aux autres membres de l'équipe.

### Q12. Quelles difficultés du DataOps ce TP a-t-il réduites, et à quelles étapes ?

- **Livraison lente :** le remote DVC et `dvc push` permettent de partager les données, tandis que `git clone` et `dvc pull` facilitent la récupération du projet par un collègue.
- **Erreurs silencieuses :** les tests unitaires et les règles de validation détectent les données invalides, tandis que les empreintes DVC permettent de détecter les changements de données.
- **« Ça marche sur ma machine » :** la combinaison de Git et DVC permet de récupérer le code et les données nécessaires pour reproduire un résultat.
- **Étapes manuelles :** les commandes standardisées de versionnement, de restauration et de récupération réduisent les manipulations improvisées. Le bonus d'automatisation DVC n'a pas été réalisé dans ce TP.

## Résultats obtenus

Les tests unitaires ont réussi : **6 tests passés**.

Résultats du pipeline :

| Version | Lignes lues | Lignes propres | Lignes rejetées | Total |
|---|---:|---:|---:|---:|
| data-v1 | 30 | 25 | 5 | 7655.90 |
| data-v2 | 35 | 30 | 5 | 8835.40 |

La restauration de `data-v1` a permis de retrouver le total de 7655.90. Le retour à `data-v2` a permis de retrouver le total de 8835.40. Le clonage du projet dans `teammate`, suivi de la récupération des données, a également produit le total de 8835.40.

## Historique Git

Sortie de `git log --oneline --graph --decorate` :

```text
* 5415444 (HEAD -> master, tag: data-v2) Data v2: late orders for 2026-10-05
* ae78780 Add the DVC remote
* cccccfc (tag: data-v1) Track raw data with DVC
*   ab7df1f Merge the country rule
|\
| * 54d9442 (feature/country-rule) Add country validation rule and DVC dependency
|/
* a93f477 Add pipeline, data checks and unit tests
* a815c4c Empty project with requirements
```

## Conclusion

Ce TP m'a permis de comprendre la différence entre le versionnement du code avec Git et le versionnement des données avec DVC. J'ai créé une branche pour ajouter une règle de validation, fusionné les modifications dans la branche principale, configuré un remote DVC, enregistré deux versions des données et restauré chacune d'elles. Enfin, le clonage du projet et la récupération des données ont confirmé la reproductibilité du pipeline.
