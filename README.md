# Urgence Territoire & Santé

Bienvenue dans le dépôt du projet **Urgence Territoire & Santé**. Ce projet vise à fournir un ensemble de *Skills* (compétences) pour Claude Code afin d'aider à la prise de décision en situation d'urgence sur un territoire donné.

## Objectif

L'objectif principal est de réduire l'empreinte idle (économie de tokens) en encapsulant la logique métier dans des scripts autonomes et testables. Chaque skill est conçu de manière minimaliste et respecte une architecture stricte pour garantir l'efficacité et la clarté.

## Skills prévus

1. **Vulnérabilité Population** : Données sociodémographiques (INSEE)
2. **Capacité Sanitaire** : Disponibilité et caractéristiques des établissements de santé
3. **Géo-Accès** : Accessibilité territoriale (BAN / IGN)
4. **Risque Industriel** : Exposition aux risques majeurs (Géorisques)
5. **Alerte Météo** : Prévisions et vigilances (Météo-France)

## Architecture d'un Skill

Chaque skill est isolé dans son propre répertoire et contient :
- `SKILL.md` : Définition ultra-concise du déclencheur et de la commande d'exécution.
- `main.py` : Script d'exécution autonome renvoyant systématiquement une sortie JSON.
- `references/` : Répertoire contenant la documentation détaillée (API, paramètres, etc.).
