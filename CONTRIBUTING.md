# Guide de contribution

## Stratégie de branches

On utilise une variante simplifiée de **Git Flow**, alignée sur nos 3 environnements
(Dev / Staging / Prod). Chaque branche a une responsabilité claire et un environnement
associé — c'est ce lien que Jenkins exploitera pour déclencher automatiquement le bon
déploiement.

| Branche      |Rôle                                                 | Déploiement Jenkins |
|--------------|-----------------------------------------------------|------------------------------------------------------|
| `main`       | Code en production, toujours stable                 |  **Prod** (déploiement manuel, approbation requise)  |
| `release/*`  | Gel de version avant mise en prod, tests de recette |  **Staging** (automatique)                           |
| `develop`    | Intégration continue des fonctionnalités terminées  |  **Dev** (automatique)                               |
| `feature/*`  | Une fonctionnalité en cours de développement        |  Aucun déploiement, seulement CI (lint + tests)      |

## Cycle de vie d'une fonctionnalité

\`\`\`
1. git checkout develop && git pull
2. git checkout -b feature/nom-de-la-fonctionnalite
3. ... développement + commits ...
4. git push origin feature/nom-de-la-fonctionnalite
5. Ouverture d'une Pull Request vers \`develop\`
6. Jenkins exécute automatiquement : lint, tests, build Docker (validation)
7. Revue de code par au moins 1 pair
8. Merge (squash) dans \`develop\`
9. Jenkins déploie automatiquement sur Dev
\`\`\`

## Règles de Pull Request

- **Jamais de commit direct sur \`main\`, \`release/*\` ou \`develop\`** — toujours via PR.
- La CI Jenkins doit être **verte** avant qu'une PR puisse être mergée (protection de
  branche à configurer côté GitHub — Settings > Branches > Branch protection rules).
- Un titre de PR clair au format \`type(scope): description\` (ex: \`feat(edge): ajout du sink MQTT\`).
- Une PR doit rester petite et focalisée sur un seul sujet.

## Convention de commits

On suit [Conventional Commits](https://www.conventionalcommits.org/) :

\`\`\`
feat(edge): ajout du sink MQTT
fix(backend): correction du timeout de connexion PostgreSQL
docs(readme): mise à jour des instructions d'installation
chore(ci): ajout du stage de scan de vulnérabilités
\`\`\`
