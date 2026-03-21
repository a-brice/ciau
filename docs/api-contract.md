# CIAU — Contrat des vues (URL contract)

Django avec Jinja2 : pas d'API REST JSON, toutes les routes renvoient des pages HTML
sauf les quelques endpoints AJAX marqués `→ JSON`.

---

## Authentification

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/login/` | Affiche le formulaire de connexion |
| `POST` | `/login/` | Vérifie le mot de passe → redirige vers `/` si OK |
| `GET` | `/logout/` | Détruit la session → redirige vers `/login/` |

---

## Tableau de bord

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/` | Liste de tous les projets actifs, avec filtres |

**Paramètres GET (filtres) :**

| Paramètre | Valeurs | Description |
|---|---|---|
| `etat` | `en_cours` / `dormant` | Filtre par état |
| `type` | `RES` / `BUR` / `IND` / … | Filtre par préfixe de référence |
| `q` | texte libre | Recherche dans désignation / maître d'ouvrage |

**Contexte Jinja2 :**
```python
{
    'projets': QuerySet[Projet],
    'nb_en_cours': int,
    'nb_livrables_urgents': int,   # deadline < 7 jours
    'nb_acomptes_retard': int,
}
```

---

## Projets

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/projets/nouveau/` | Formulaire de création |
| `POST` | `/projets/nouveau/` | Crée le projet → redirige vers `/projets/<id>/` |
| `GET` | `/projets/<id>/` | Fiche de suivi complète |
| `GET` | `/projets/<id>/modifier/` | Formulaire de modification |
| `POST` | `/projets/<id>/modifier/` | Enregistre les modifications → redirige vers `/projets/<id>/` |
| `POST` | `/projets/<id>/archiver/` | Passe le projet en `archive` → redirige vers `/` |
| `POST` | `/projets/<id>/supprimer/` | Supprime le projet → redirige vers `/` |

**Contexte fiche projet (`GET /projets/<id>/`) :**
```python
{
    'projet': Projet,
    'livrables': QuerySet[Livrable],        # ordonnés par ordre de phase
    'acomptes': QuerySet[Acompte],          # ordonnés par numéro
    'references': QuerySet[Reference],
    'solde': Decimal,                       # calculé : sum(encaissé) - honoraires
    'progression': int,                     # % de phases validées
}
```

---

## Livrables (phases d'études)

| Méthode | URL | Description |
|---|---|---|
| `POST` | `/projets/<id>/livrables/ajouter/` | Ajoute une phase → redirige vers fiche |
| `POST` | `/projets/<id>/livrables/<lid>/modifier/` | Met à jour état / commentaire / deadline |
| `POST` | `/projets/<id>/livrables/<lid>/upload/` | Upload d'un fichier → enregistre dans `uploads/<id>/livrables/` |
| `POST` | `/projets/<id>/livrables/<lid>/supprimer/` | Supprime la phase |

**Champs du formulaire `modifier` :**

| Champ | Type | Description |
|---|---|---|
| `etat` | select | `a_faire` / `en_cours` / `livre` / `valide` |
| `commentaire` | textarea | Observations libres |
| `deadline` | date | Date limite de remise |

---

## Acomptes

| Méthode | URL | Description |
|---|---|---|
| `POST` | `/projets/<id>/acomptes/ajouter/` | Ajoute un acompte → redirige vers fiche |
| `POST` | `/projets/<id>/acomptes/<aid>/encaisser/` | Marque comme reçu + date d'encaissement |
| `POST` | `/projets/<id>/acomptes/<aid>/modifier/` | Modifie montant / déclenchement / échéance |
| `POST` | `/projets/<id>/acomptes/<aid>/supprimer/` | Supprime l'acompte |

**Champs du formulaire `ajouter` :**

| Champ | Type | Description |
|---|---|---|
| `numero` | integer | Numéro d'ordre |
| `declenchement` | text | Description de l'événement déclencheur |
| `montant` | decimal | Montant en FCFA |
| `date_echeance` | date | Date d'échéance prévue |

**Champs du formulaire `encaisser` :**

| Champ | Type | Description |
|---|---|---|
| `date_encaissement` | date | Date de réception effective |

---

## Références / Documents

| Méthode | URL | Description |
|---|---|---|
| `POST` | `/projets/<id>/references/ajouter/` | Ajoute une référence (lien ou fichier) |
| `POST` | `/projets/<id>/references/<rid>/supprimer/` | Supprime la référence |

**Champs du formulaire `ajouter` :**

| Champ | Type | Description |
|---|---|---|
| `type` | select | `document` / `lien` / `contact` / `autre` |
| `libelle` | text | Nom affiché |
| `valeur` | text | URL, email, numéro… |
| `fichier` | file | Upload optionnel → `uploads/<id>/references/` |

---

## Activités hebdomadaires

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/activites/` | Fiche de la semaine courante |
| `GET` | `/activites/?semaine=2026-02-16` | Fiche d'une semaine spécifique (lundi) |
| `POST` | `/activites/saisir/` | Enregistre les activités de la semaine |
| `GET` | `/activites/export/?semaine=2026-02-16` | Export PDF de la fiche semaine |

**Contexte (`GET /activites/`) :**
```python
{
    'semaine_debut': date,
    'semaine_fin': date,
    'intervenants': QuerySet[Intervenant],
    'activites': dict[intervenant_id, list[Activite]],
}
```

---

## Registre des contrats

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/contrats/` | Liste de tous les contrats |
| `GET` | `/contrats/?etat=en_cours` | Filtré par état |

**Contexte :**
```python
{
    'contrats': QuerySet[Projet],   # projets avec contrat renseigné
}
```

---

## Archives

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/archives/` | Liste des projets archivés |

---

## Exports

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/projets/<id>/export/pdf/` | Export PDF de la fiche de suivi |
| `GET` | `/projets/<id>/export/csv/` | Export CSV des acomptes du projet |
| `GET` | `/activites/export/?semaine=YYYY-MM-DD` | Export PDF fiche activité semaine |

---

## Convention de réponses

- Toutes les vues `POST` réussissent avec un **redirect** (pattern PRG — Post/Redirect/Get).
- En cas d'erreur de formulaire, la vue re-rend le template avec les erreurs dans le contexte.
- Les suppressions sont des `POST` (pas de `DELETE`) pour compatibilité formulaire HTML.
- Aucun endpoint ne renvoie de JSON sauf cas explicitement marqué `→ JSON` (réservé pour futures interactions AJAX si nécessaire).
