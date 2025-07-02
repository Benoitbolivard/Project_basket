# 🏀 Scoreboard Basket

Ce projet est une application web légère et responsive destinée à la gestion **manuelle** du score et des principaux événements d’un match de basketball.  
**L’objectif principal** est de fournir un outil accessible, rapide à prendre en main, utilisable depuis n’importe quel appareil (PC, tablette, smartphone), sans aucune installation ni compétence technique.

## But du projet

Le but de ce dépôt est de proposer une solution pratique pour :
- **Animer des matchs de basket** amateurs, scolaires, associatifs ou de loisir, sans matériel spécifique
- **Rendre accessible le suivi du score** et des temps de jeu à toute personne, même non technicienne ou non arbitre
- **Remplacer un panneau de score physique** en situation de dépannage, ou lors de matchs amicaux en extérieur
- **Faciliter la gestion du temps, des fautes et temps-morts** lors de petits tournois, événements sportifs, journées d’animation, etc.
- **Standardiser la présentation du score** sur un support visible de tous (ex : vidéoprojecteur, écran partagé, smartphone posé en bord de terrain)
- **Gagner du temps lors de l’installation**, tout se faisant via un simple navigateur

Ce projet vise à aider :
- Les professeurs d’EPS, animateurs, entraîneurs ou bénévoles
- Les organisateurs de tournois ou d’événements sportifs locaux
- Les équipes loisirs et clubs amateurs de basket
- Toute personne souhaitant simplement tenir le score facilement, sans matériel dédié

---

## Fonctionnalités

- Configuration du match (noms des équipes, durée des périodes, nombre de temps-morts)
- Gestion du score (+1, +2, +3 pour chaque équipe)
- Chronomètre de période avec gestion de la pause/reset
- Affichage et gestion de la possession
- Suivi des fautes d’équipe et du bonus
- Suivi des temps-morts par équipe
- Interface responsive adaptée aux tablettes et mobiles

---

## Structure du dépôt

```

scoreboard-basket/
├── index.html        # Fichier principal de l’application (tout-en-un)
├── README.md         # Ce fichier de documentation
├── assets/           # (optionnel) Images, sons, ressources statiques
│   └── buzzer.mp3    # Exemple : son pour la fin de période
├── css/              # (optionnel) Feuilles de styles externes
│   └── style.css
├── js/               # (optionnel) Scripts JS séparés
│   └── main.js

````

> **Remarque** :  
> Par défaut, le projet fonctionne uniquement avec `index.html` qui contient tout le code.  
> Tu peux séparer le CSS et le JS dans les dossiers correspondants si besoin.

---

## Installation & utilisation

Aucune installation n’est requise !  
Il suffit d’ouvrir le fichier `index.html` dans ton navigateur préféré.

1. Clone ce dépôt ou télécharge-le :
    ```bash
    git clone https://github.com/votre-utilisateur/scoreboard-basket.git
    ```
2. Ouvre `index.html`
3. Renseigne les paramètres du match et clique sur « Commencer le match »
4. Gère le score, les fautes et le chrono pendant la partie

---

## Personnalisation

- **Logo/nom** : Tu peux ajouter un logo ou changer les couleurs dans la partie `<style>`.
- **Durées par défaut** : Modifie les valeurs dans la liste des périodes.
- **Langue** : L’application est en français mais tu peux la traduire facilement.

---

## Auteurs

- Réalisé par Benoit Bolivard

---

## Licence

Ce projet est libre de droits, tu peux l’utiliser, le modifier et le partager sans restriction.

---

**Bonne utilisation et bon match !** 🏀
````


