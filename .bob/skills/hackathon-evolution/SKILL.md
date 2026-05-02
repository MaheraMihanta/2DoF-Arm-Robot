---
name: hackathon-evolution
description: Transformer le bras robotique 2DDL en demonstration hackathon IBM Bob avec ameliorations visibles, tests et documentation.
---

Utilise ce skill quand l'utilisateur demande d'adapter, ameliorer, presenter ou documenter ce projet pour le hackathon IBM Bob.

## Objectif

Faire evoluer le projet existant sans le reconstruire inutilement. Le resultat doit montrer concretement la valeur de Bob: comprehension du code, choix d'une amelioration utile, implementation controlee, tests, documentation et preparation de la demo.

## Workflow

1. Comprendre la demande et identifier si elle vise:
   - une amelioration fonctionnelle;
   - une meilleure demonstration;
   - une documentation ou un pitch;
   - une integration d'outil externe ou MCP;
   - une correction de bug.

2. Lire uniquement les fichiers necessaires:
   - `README.md` et `QUICKSTART.md` pour le contexte utilisateur;
   - `phase1_simulation/kinematics.py` pour la cinematique et les trajectoires;
   - `phase1_simulation/config.py` pour les limites physiques;
   - `phase3_integration/robot_controller.py` et `phase3_integration/gui.py` pour les workflows complets;
   - `tests/` pour les patterns de validation.

3. Proposer ou choisir une amelioration demonstrable en moins de 5 minutes devant un jury.

4. Implementer avec un perimetre court:
   - logique de calcul dans `phase1_simulation/` ou `phase3_integration/`;
   - interface ou demo dans `phase3_integration/gui.py` si necessaire;
   - tests dans `tests/`;
   - documentation dans `README.md`, `QUICKSTART.md` ou `docs/`.

5. Verifier:
   - lancer `python -m pytest tests -v`;
   - tester le mode simulation avant toute mention du mode hardware;
   - decrire les limites connues si le materiel n'a pas ete teste.

## Idees d'ameliorations adaptees au hackathon

- Ajout d'un validateur de trajectoire qui detecte positions inatteignables, singularites et angles hors limites avant execution.
- Ajout d'un mode demo automatique: carre, cercle, zigzag, puis resume des positions et erreurs.
- Export d'un rapport Markdown ou CSV de trajectoire pour montrer les points, angles et validations.
- Amelioration de l'interface graphique avec un panneau "Demo hackathon" montrant etat, trajectoire active, erreurs et bouton d'arret.
- Ajout de tests de non-regression pour les trajectoires polyline, cercle et limites de workspace.
- Creation d'un script de pitch technique qui explique le role de Bob dans l'evolution du projet.

## Regles de securite

- Ne jamais envoyer de commande GRBL reelle sans confirmation explicite.
- En cas de doute, rester en `ControlMode.SIMULATION`.
- Toute trajectoire doit etre rejetee si un point n'a pas de solution de cinematique inverse.
- Les conversions radians/degres doivent etre explicites dans les noms de variables ou l'affichage.

## Format de reponse attendu

Quand une evolution est terminee, repondre avec:

- ce qui a ete ajoute;
- les fichiers modifies;
- les commandes de test executees;
- la facon de lancer la demonstration;
- une courte phrase expliquant pourquoi cette evolution met IBM Bob en valeur.
