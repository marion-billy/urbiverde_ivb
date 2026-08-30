# Chapitre 6 (retour d'expérience) — trame de questions à remplir

> But : débloquer la rédaction du chapitre le plus déterminant pour la note « travail d'ingénieur »
> du jury SIGMA. Réponds en style télégraphique (quelques mots, des chiffres, des faits) sous chaque
> question — pas besoin de rédiger, je m'en charge. Laisse vide ce qui ne s'applique pas. Ce que le
> jury cherche dans ce chapitre : **autonomie, méthode, capacité à justifier et à prendre du recul
> critique, insertion professionnelle, difficultés surmontées, montée en compétence**.

---

## 6.1. Conduite de projet — déroulé, planning, insertion

*Ce que le jury note ici : ta capacité à piloter un projet (planifier, réajuster) et à travailler
dans une équipe / un consortium.*

**Planning**
1. Quelles grandes étapes / jalons avais-tu prévus au départ ? Sur quelles durées (le Gantt prévisionnel de `planning_stage_Marion_010326.xlsx`) ?
2. Qu'est-ce qui a **glissé** par rapport au prévisionnel, de combien, et **pourquoi** ? (p. ex. le temps pris par la fiabilisation, la performance, les changements de méthode.)
3. Quand et pourquoi Toulouse a-t-elle été **ajoutée en cours de route** comme ville de contrôle ?
4. Quand le **resserrement du périmètre** (vers une V1 fonctionnelle) a-t-il été décidé, et par qui / sur quel constat ?

**Insertion équipe / encadrement**
5. À quel **rythme** les points avec l'encadrement ? (1v1 avec le tuteur ? avec Hugo ? à quelle fréquence, quel jour ?)
6. Les **réunions d'équipe R&D** : à quelle fréquence ? Portaient-elles sur la veille, les difficultés, des présentations de tes sujets aux autres (supports, quiz) ? Décris **une** occasion concrète.
7. Ton **rôle** dans l'équipe (ce dont tu étais responsable, seule ou en binôme) ?

**Consortium & utilisateurs (UrbiVerde : CS Group, Cerema, Aerospace Valley)**
8. As-tu **interagi avec le consortium** ? À quelles occasions (réunions, livrables, ateliers) ?
9. Y a-t-il eu des **ateliers avec les villes / utilisateurs** ? Qui, quand ?
10. Un **retour utilisateur a-t-il changé un choix de conception** ? (p. ex. la lisibilité de la restitution / du tableau de bord.) Lequel, et qu'as-tu changé ?

---

## 6.2. Choix de méthode : essais et alignement — *déjà rédigé, à compléter*

*Le récit de l'alignement Cerema et de la différenciation (profils, données, 5→4) est déjà en place.
Vérifie et enrichis :*

11. Une **piste explorée puis abandonnée** non encore mentionnée (un essai qui n'a pas abouti) ?
12. L'alignement Cerema : combien d'**échanges**, sous quelle forme (mail / visio / réunion) ? Un **désaccord ou ajustement marquant** avec leurs chercheurs ?

---

## 6.3. Débogage et fiabilisation — *déjà rédigé, à confirmer*

*Le récit des anomalies (graphe, lissage des nœuds, moindre coût à 1 pixel) et des cas limites
(grande tache, données dégradées) est en place. Confirme / précise :*

13. **Comment repérais-tu** les anomalies ? (comparaison visuelle systématique sur Toulouse ? autre ?)
14. **Comment les résolvais-tu** ? (agent IA pour explorer/réécrire, échanges avec le tuteur pour trancher, documentation des bibliothèques — dans quelles proportions ?)
15. **Un bug particulièrement instructif** à raconter (le plus formateur) ?

---

## 6.4. Performance et passage à l'échelle — *déjà rédigé (tableau des temps)*

16. Rien d'obligatoire. Veux-tu **commenter ce que l'optimisation t'a appris** (profilage, vectorisation, index spatial) en une phrase de recul ?

---

## 6.5. Environnement de travail et assistance par IA — *déjà rédigé, à valider*

*La description sobre de la convention Claude (pour un jury peu familier de l'IA) est en place. Vérifie :*

17. Le **setup exact** est-il correct : VSCode connecté à une VM distante OVH (350 Go RAM, 24 cœurs, GPU H100) ? Corrige si besoin.
18. Ta **méthode de travail au quotidien** (ton « train of thoughts ») : comment tu enchaînais lecture / test / validation du code produit ? Une phrase.
19. Un exemple concret où **la posture sceptique de l'assistant t'a évité une erreur** (ou l'inverse : une sortie qu'il a fallu corriger) ?

---

## 6.6. Organisation, reproductibilité et passation — *déjà rédigé, à confirmer*

20. **Emplacement du dépôt** Git et **documentation effectivement laissée** à la fin du stage (README ? journal ? vue notebooks ?) — à confirmer.
21. La passation : tu **restes dans l'équipe** (contrat) et sa poursuite permettra d'achever la mise en production. Confirmes-tu cette formulation ?

---

## 6.7. Apports personnels — *le plus important pour la note, presque tout à écrire*

*Ce que le jury note ici : ta montée en compétence d'ingénieure, et ta capacité à prendre du recul
critique sur ton propre travail. Réponds franchement, c'est ce qui pèse.*

**Compétences techniques acquises ou consolidées** (coche/complète)
22. Python géospatial (xarray, geopandas, networkx, scikit-image) : acquis / consolidé / déjà maîtrisé ?
23. Théorie des graphes appliquée à l'écologie du paysage ?
24. Chaîne d'observation de la Terre (Google Earth Engine, OpenStreetMap) ?
25. Optimisation / passage à l'échelle (profilage, vectorisation) ?
26. Autre compétence technique marquante ?

**Compétence « métier » centrale**
27. Traduire un **modèle écologique en chaîne reproductible** et en **couches actionnables pour des non-spécialistes** : en quoi est-ce le cœur de ce que tu as appris ? (une ou deux phrases de ta main serait idéal)

**Compétences non techniques**
28. Travail en **consortium** / dialogue avec des **utilisateurs** non spécialistes : qu'as-tu appris ?
29. Gérer un **périmètre mouvant** (savoir resserrer, prioriser) : qu'en retires-tu ?
30. **Rigueur et traçabilité** (journal de décisions, convention, contrôles automatisés) : est-ce une pratique que tu as adoptée ?

**Recul critique (très valorisé par SIGMA)**
31. Qu'est-ce que tu **referais différemment** si tu recommençais le stage ?
32. Quelle **limite de ton travail** assumes-tu le plus lucidement (au-delà des limites techniques du chapitre 4) ?

**Projet professionnel**
33. En quoi ce stage a-t-il **précisé ton projet professionnel** (tu poursuis dans l'équipe) ?

---

> Quand tu as rempli, renvoie-moi le fichier (ou colle tes réponses) : je transforme en prose sobre,
> à la première personne, au registre du chapitre 6, sans em dash et sans emphase.
