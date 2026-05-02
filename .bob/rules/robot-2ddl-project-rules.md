# Regles projet - Bras robotique 2DDL

Ces regles s'appliquent a toutes les conversations IBM Bob dans ce depot.

## Identite du projet

- Le projet est un bras robotique 2DDL asservi en position, avec simulation, interface materielle GRBL/A4988, interface graphique et documentation.
- L'objectif hackathon est de montrer comment IBM Bob aide a comprendre, ameliorer, tester et documenter un projet existant, pas de masquer le travail deja realise.
- Toute amelioration doit rester demontrable en simulation sans materiel, puis compatible avec le mode hardware quand c'est pertinent.

## Structure a respecter

- `phase1_simulation/` contient la configuration, la cinematique directe/inverse, la jacobienne et les trajectoires.
- `phase2_hardware/` contient la communication GRBL, la conversion angles/pas et les parametres A4988.
- `phase3_integration/` contient le controleur principal et l'interface graphique.
- `tests/` contient les tests unitaires Pytest.
- `docs/` contient les explications techniques et le rapport LaTeX.

## Contraintes techniques

- Les angles internes sont en radians; les affichages utilisateur peuvent etre en degres.
- Les positions cartesiennes sont en millimetres.
- Ne pas contourner `RobotConfig.is_angle_valid` ni les controles d'accessibilite de la cinematique inverse.
- Une position non atteignable doit etre traitee explicitement, jamais convertie en mouvement silencieux.
- En mode hardware ou hybrid, ne jamais lancer de mouvement reel sans confirmation claire de l'utilisateur.
- Toute nouvelle trajectoire doit etre validee point par point avec la cinematique inverse avant execution.

## Style de code

- Preferer des changements petits, lisibles et localises.
- Reutiliser les classes existantes: `Kinematics`, `RobotConfig`, `RobotController`, `MotorController` et `GRBLInterface`.
- Garder les fonctions de calcul independantes de l'interface graphique quand c'est possible.
- Ajouter des tests Pytest pour toute logique de cinematique, trajectoire, validation de securite ou conversion.
- Eviter les dependances lourdes si `numpy`, `matplotlib`, `pygame`, `pyserial`, `pytest` suffisent.

## Workflow Bob recommande

- Pour une nouvelle fonctionnalite importante, commencer en mode Plan, puis implementer en mode Code.
- Pour une tache complexe avec recherche web, MCP ou plusieurs outils, utiliser Advanced.
- Avant d'editer, identifier les fichiers touches et expliquer brievement l'intention.
- Apres edition, lancer au minimum `python -m pytest tests -v` si le changement touche le code Python.
- Mettre a jour `README.md`, `QUICKSTART.md` ou `docs/` quand une fonctionnalite visible est ajoutee.

## Documentation et demonstration

- Rediger les explications en francais clair.
- Pour le hackathon, documenter a chaque amelioration:
  - le probleme de depart;
  - ce que Bob a aide a faire;
  - les fichiers modifies;
  - les tests ou validations;
  - la valeur demonstrable pour un jury.
- Preferer une demo courte, fiable et visuelle: simulation, trajectoires predefinies, validation de securite, export de rapport ou interface GUI.
