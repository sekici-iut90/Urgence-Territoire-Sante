# 🚨 Urgence Territoire & Santé

> **Plugin Claude Code pour opérateurs de crise** — Transformez Claude en assistant opérationnel de Centre Opérationnel Départemental (COD).

---

## 🎯 Le cas d'usage

Lors d'une catastrophe (inondation, explosion industrielle, vague de chaleur...), les opérateurs des **préfectures, SDIS et SAMU** doivent prendre des décisions critiques en quelques minutes avec des données dispersées sur des dizaines de plateformes.

Ce plugin transforme Claude en un **assistant de COD** capable d'agréger instantanément les données vitales sur n'importe quelle zone sinistrée : combien de personnes âgées à évacuer ? Quel hôpital est disponible ? Y a-t-il un site Seveso à proximité ? La réponse arrive en langage naturel, en quelques secondes.

---

## ⚙️ Les 5 Capacités Opérationnelles

| # | Skill | Utilité en situation de crise | Source |
|---|-------|-------------------------------|--------|
| 1 | 👥 **Vulnérabilité Population** | Dimensionner les évacuations en identifiant la part de personnes âgées, de logements surpeuplés et de populations à mobilité réduite dans un quartier. | INSEE |
| 2 | 🏥 **Capacité Sanitaire** | Localiser en temps réel les hôpitaux, cliniques et EHPAD disponibles dans un rayon donné et connaître leur capacité d'accueil résiduelle. | data.gouv.fr |
| 3 | 🗺️ **Géo-Accès** | Évaluer l'accessibilité routière d'une zone (routes coupées, temps d'accès) pour optimiser l'acheminement des secours et des évacuations. | BAN / IGN |
| 4 | ⚠️ **Risque Industriel** | Identifier immédiatement les sites Seveso, dépôts de matières dangereuses et périmètres de sécurité dans la zone sinistrée pour prévenir les sur-accidents. | Géorisques |
| 5 | 🌩️ **Alerte Météo** | Intégrer les prévisions et vigilances météorologiques (vent, pluie, chaleur) pour anticiper l'évolution de la crise et adapter les dispositifs. | Météo-France |

---

## 🛠️ Pour les développeurs — Architecture & Économie de Tokens

Ce projet fait le choix délibéré de **ne pas utiliser l'approche MCP classique** (Model Context Protocol), qui charge en permanence des définitions d'outils lourdes dans le contexte de l'IA, consommant des tokens inutilement même en veille.

À la place, nous utilisons le concept de **Skills** :

- Chaque skill possède un `SKILL.md` **ultra-court (< 60 tokens)**, qui ne contient qu'un déclencheur sémantique (`Trigger when user asks...`) et la commande d'exécution. L'IA ne charge ce fichier que si le contexte l'exige.
- La logique métier réside dans un `main.py` **autonome et testable en ligne de commande**, qui génère du JSON propre sur `stdout`. Zéro dépendance à l'environnement Claude.
- La documentation détaillée (paramètres API, schémas, codes d'erreur) est reléguée dans `references/api.md`, jamais chargée automatiquement.

```
skill-name/
├── SKILL.md           # < 60 tokens — déclencheur + commande
├── main.py            # Script autonome → stdout JSON
└── references/
    └── api.md         # Documentation technique complète
```

> Ce design garantit une **empreinte idle quasi nulle** et une séparation nette entre le signal (SKILL.md) et la documentation (references/).

## 🤖 Mode Multi-Agents 

En plus des compétences CLI individuelles, ce plugin déploie une **cellule de crise multi-agents** locale via la commande native `/agents` de Claude Code. 

- `coordonnateur` : Le dispatcher principal du COD qui reçoit l'alerte et orchestre la récolte de données.
- `expert_population` / `expert_risques` / `expert_meteo` / `expert_geo` / `expert_health` : Des agents thématiques dotés de fiches d'instructions spécifiques et aux privilèges d'outils (`allowed-tools`) bridés à leur strict périmètre technique.

Pour lancer une simulation complète de gestion de crise :
```bash
/agents coordonnateur
> "Explosion signalée à Belfort avec début d'incendie, évaluez la situation globale."