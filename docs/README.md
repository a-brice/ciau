# CIAU — Documentation du Projet

**Application web de gestion de projets pour Ciau Architecture**

---

## Table des matières

1. [Vision du produit](#1-vision-du-produit)
2. [Modèle de données](#2-modèle-de-données)
3. [Fonctionnalités](#3-fonctionnalités)
4. [Flux de travail](#4-flux-de-travail)
5. [Glossaire](#5-glossaire)

> **Autres documents :**
> - [`technical.md`](./technical.md) — Stack, structure du projet, accès, stockage fichiers
> - [`api-contract.md`](./api-contract.md) — Contrat des routes et vues Django

---

## 1. Vision du produit

CIAU est une application web interne destinée au cabinet **Ciau Architecture**. Elle numérise et centralise les outils de suivi aujourd'hui gérés dans des fichiers Excel :

| Feuille Excel actuelle | Équivalent dans l'app |
|---|---|
| `Liste de projets` | Tableau de bord — liste de tous les projets |
| `Fiche de Suivi` | Fiche projet individuelle (livrables + finances) |
| `Fiche Activité CIAU` | Journal d'activité hebdomadaire par intervenant |
| `Liste des contrats` | Registre des contrats |
| `Archives` | Projets archivés / clôturés |

### Objectifs

- Remplacer les tableurs Excel dispersés par une interface unique.
- Donner une visibilité en temps réel sur l'état de chaque projet.
- Suivre les flux financiers (honoraires, acomptes, solde) par projet.
- Coordonner les activités hebdomadaires des intervenants.

---

## 2. Modèle de données

### 2.1 Projet

Entité centrale. Correspond à une ligne de la feuille `Liste de projets`.

| Champ | Type | Source Excel | Description |
|---|---|---|---|
| `id` | UUID | — | Identifiant unique |
| `item` | integer | `ITEM` | Numéro d'ordre (ex. 23) |
| `reference` | string | `REFERENCE` | Code de référence (ex. `RES/1118/PR`) |
| `designation` | string | `DESIGNATION` | Intitulé complet du projet |
| `maitre_ouvrage` | string | `MAÎTRE D'OUVRAGE` | Nom du client / maître d'ouvrage |
| `contrat_moe` | string | `CONTRAT MOE` | Statut du contrat de maîtrise d'œuvre |
| `etat` | enum | `ETAT` | Voir [§2.2](#22-états-dun-projet) |
| `phase_actuelle` | string | `PHASE ACTUELLE` | Phase en cours (ex. `APS`, `DCE`) |
| `potentiel` | boolean | `Potentiel` | Projet potentiel non encore contractualisé |
| `honoraires` | decimal | (fiche suivi) | Montant total des honoraires en FCFA |
| `solde` | decimal | `SOLDE` | Solde financier courant |
| `created_at` | datetime | — | Date de création |
| `updated_at` | datetime | — | Dernière modification |

### 2.2 États d'un projet

Issus des valeurs réelles de la colonne `ETAT` du fichier Excel :

| Valeur | Libellé | Description |
|---|---|---|
| `en_cours` | En cours | Projet actif avec des études ou travaux en progression |
| `dormant` | Dormant | Projet en attente (client, financement, administration) |
| `archive` | Archivé | Projet terminé ou abandonné, visible en lecture seule |

Statuts du contrat MOE (`CONTRAT MOE`) :

| Valeur | Description |
|---|---|
| `Signé et en suivi` | Contrat signé, projet actif |
| `Projet de contrat` | Contrat en cours de négociation |
| `Contrat à vérifier` | Contrat dont le statut doit être confirmé |

### 2.3 Référence projet

Format des codes de référence utilisés par Ciau Architecture :

| Préfixe | Type de projet |
|---|---|
| `RES/` | Résidentiel (Privé) |
| `BUR/` | Bureaux |
| `REB/` | Résidentiel & Bureaux |
| `HOT/` | Hôtel |
| `HOS/` | Hospitalier |
| `PRI/` | Programme Immobilier |
| `IND/` | Industriel / Institutionnel |
| `Villa` | Villa individuelle |
| `IR` | Immeuble Résidentiel |
| `BOAD` | Projets client BOAD |

Exemple : `RES/1118/PR`, `Villa04/06-024/LT`, `BOAD 06/2024/LT`

### 2.4 Livrable (Phase d'études)

Chaque projet comporte des phases d'études standardisées (architecture). Source : section `LIVRABLES (États d'avancement)` de la feuille `Fiche de Suivi`.

| Phase | Libellé complet |
|---|---|
| `EP` | Études Préliminaires |
| `APS` | Avant-Projet Sommaire |
| `APD` | Avant-Projet Détaillé |
| `IPC` | Instruction du Permis de Construire |
| `PCG` | Projet de Conception Général |
| `DCE` | Dossier de Consultation des Entreprises |
| `MDT` | Mise au Point des Marchés de Travaux |
| `Travaux` | Phase chantier / suivi des travaux |

| Champ | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique |
| `projet_id` | UUID | Référence au projet |
| `phase` | enum | Code de la phase (EP, APS, etc.) |
| `etat` | enum | `a_faire` / `en_cours` / `livre` / `valide` |
| `commentaire` | text | Observations (ex. "Esquisses livrées, attente retour client") |
| `deadline` | date | Date limite de remise |
| `fichier_url` | string | Lien vers le document déposé (optionnel) |

### 2.5 Acompte

Versement prévu au contrat, déclenché par une étape précise. Source : colonne `COMPTABILITE` de la fiche de suivi.

| Champ | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique |
| `projet_id` | UUID | Référence au projet |
| `numero` | integer | Numéro d'ordre (Acompte 1, 2, …) |
| `declenchement` | text | Événement déclencheur (ex. "À la signature du contrat") |
| `montant` | decimal | Montant en FCFA |
| `date_echeance` | date | Date d'échéance attendue |
| `date_encaissement` | date | Date de réception effective (null si non reçu) |
| `statut` | enum | `en_attente` / `recu` / `en_retard` |

> Le **solde** est calculé automatiquement : `somme des acomptes reçus - honoraires totaux`.

**Exemple réel (projet IR6/02-2023/LT — Honoraires : 52 500 000 FCFA) :**

| N° | Déclenchement | Montant |
|---|---|---|
| 1 | À la signature du contrat de maîtrise d'œuvre | 8 500 000 |
| 2 | À la remise de l'Avant-Projet | 10 000 000 |
| 3 | À la remise du Projet Définitif + IPC | 5 000 000 |
| 4 | À la remise des Plans d'exécution + DQE | 9 000 000 |
| 5 | À la notification de démarrage des travaux | 5 000 000 |
| 6 | Solde par décomptes mensuels (travaux) | 15 000 000 |
| **Total** | | **52 500 000** |

### 2.6 Intervenant

Membres de l'équipe Ciau Architecture, issus de la `Fiche Activité CIAU` :

| Rôle | Nom actuel |
|---|---|
| Responsable Administratif et Financier | M. Eric KOUMADO |
| Responsable Technique Architecture | M. Cédric GBAGBA |
| Responsable Technique Œuvres Secondaires | M. Augustin AKOUVI |
| Logistique & Divers | Mlle Pierrette TCHINDI |

| Champ | Type | Description |
|---|---|---|
| `id` | integer | Identifiant unique |
| `nom` | string | Nom complet |
| `poste` | string | Intitulé du poste dans le cabinet |

### 2.7 Activité hebdomadaire

Correspond à la feuille `Fiche Activité CIAU` — journal des tâches par semaine et par intervenant.

| Champ | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique |
| `intervenant_id` | UUID | Référence à l'intervenant |
| `projet_id` | UUID | Référence au projet concerné (optionnel) |
| `semaine_debut` | date | Premier jour de la semaine (lundi) |
| `activite` | text | Description de l'activité réalisée |
| `delai` | date | Délai associé à l'activité |
| `observations` | text | Commentaires libres |

### 2.8 Référence / Document associé

Liens et documents rattachés à un projet (contrats, plans, contacts client…).

| Champ | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique |
| `projet_id` | UUID | Référence au projet |
| `type` | enum | `document` / `lien` / `contact` / `autre` |
| `libelle` | string | Nom affiché |
| `valeur` | string | URL, chemin, numéro, email |

---

## 3. Fonctionnalités

### 3.1 Tableau de bord — Liste de projets

Vue principale correspondant à la feuille `Liste de projets`.

- Liste paginée de tous les projets avec : référence, désignation, maître d'ouvrage, statut contrat, état, phase actuelle.
- Filtrage par état (`En cours` / `Dormant` / `Archivé`), type de projet (préfixe de référence), intervenant.
- Indicateurs globaux : nombre de projets en cours, livrables à rendre cette semaine, acomptes en retard.
- Bouton de création d'un nouveau projet.
- Accès rapide à la fiche de chaque projet.

### 3.2 Fiche de suivi projet

Page détaillée d'un projet, reflétant la feuille `Fiche de Suivi`.

#### Bloc Identité
- Référence, désignation, maître d'ouvrage.
- Responsable des études, consultant extérieur.
- Descriptif libre du projet.
- État et phase actuelle (modifiables).

#### Bloc Livrables / Phases d'études
- Liste ordonnée des phases (EP → APS → APD → IPC → PCG → DCE → MDT → Travaux).
- État de chaque phase avec case à cocher ou sélecteur.
- Champ commentaire par phase (ex. "Esquisses livrées, attente retour client").
- Upload de documents associés.
- Barre de progression globale (ex. `4/8 phases validées`).

#### Bloc Comptabilité
- Montant total des honoraires.
- Tableau des acomptes : numéro, déclenchement, montant, statut, date d'encaissement.
- Solde calculé automatiquement.
- Indicateur visuel : solde positif (encaissements > attendu) ou négatif.

#### Bloc Références & Documents
- Liens vers contrats, plans, contacts client.
- Ajout / suppression de références.

#### Bloc Historique
- Journal des modifications (qui, quand, quoi).

### 3.3 Fiche Activité hebdomadaire

Correspondant à la feuille `Fiche Activité CIAU`.

- Saisie des activités par semaine et par intervenant.
- Vue par semaine avec navigation avant/arrière.
- Champs : activité, délai, observations — par intervenant.
- Export PDF de la fiche activité de la semaine.

### 3.4 Registre des contrats

Correspondant à la feuille `Liste des contrats`.

- Liste des contrats : référence, désignation, état, déclenchement de facturation, observations.
- Lien vers la fiche projet correspondante.

### 3.5 Archives

Correspondant à la feuille `Archives`.

- Projets clôturés, accessibles en lecture seule.
- Affichage des colonnes : référence, désignation, maître d'ouvrage, honoraires, solde final.

### 3.6 Alertes et notifications

- Livrables dont la deadline approche (< 7 jours) ou dépassée.
- Acomptes en retard (date d'échéance dépassée, non encaissé).
- Projets sans activité enregistrée depuis plus de 30 jours.

---

## 4. Flux de travail

### Cycle de vie d'un projet

```
[Nouveau] → En cours → Archivé
               ↕
            Dormant
```

### Création d'un projet

1. Depuis le tableau de bord, cliquer sur "Nouveau projet".
2. Renseigner : référence (selon la nomenclature Ciau), désignation, maître d'ouvrage, état.
3. Ajouter les phases d'études applicables avec leurs deadlines.
4. Saisir le plan d'acomptes contractuel (montants + événements déclencheurs).
5. Attacher les références utiles (contrat signé, coordonnées client, etc.).

### Suivi en cours de projet

- Mettre à jour l'état des phases au fil de l'avancement.
- Marquer les acomptes comme reçus avec la date d'encaissement.
- Le solde se recalcule automatiquement.
- Saisir la fiche activité hebdomadaire par intervenant.

### Archivage

1. Toutes les phases sont validées et le solde est soldé.
2. Passer le projet en `Archivé`.
3. La fiche est déplacée dans la section Archives, accessible en lecture seule.

---

## 5. Glossaire

| Terme | Définition |
|---|---|
| **Maître d'ouvrage** | Client donneur d'ordre du projet |
| **Contrat MOE** | Contrat de Maîtrise d'Œuvre signé entre Ciau Architecture et le client |
| **Phase / Livrable** | Étape contractuelle d'études à produire (EP, APS, APD, etc.) |
| **Honoraires** | Montant total dû à Ciau Architecture pour la mission |
| **Acompte** | Versement partiel prévu au contrat, déclenché par une étape précise |
| **Solde** | Différence entre total encaissé et honoraires totaux |
| **Dormant** | Projet en pause sans activité en cours |
| **Fiche de suivi** | Document centralisé par projet regroupant identité, livrables et comptabilité |
| **Fiche activité** | Journal hebdomadaire des tâches par intervenant |
