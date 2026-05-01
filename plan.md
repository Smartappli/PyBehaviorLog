# Plan d'implémentation restant BORIS/CowLog

## Objectif
Atteindre une compatibilité fonctionnelle plus complète avec les formats récents BORIS/CowLog,
au-delà de la compatibilité actuelle orientée import/export principal.

## 1) Stabiliser la base de compatibilité (priorité haute)
- [ ] **Versionner explicitement les extensions maison** (ex. métadonnées CowLog enrichies, préfixes d'observation fusionnées).

## 2) Compléter la fidélité BORIS (priorité haute)
- [ ] **Importer/exporter toutes les observations BORIS sans perte de contexte**:
  - identifiants d'observation
  - médias synchronisés par observation
  - variables par observation
  - commentaires/notes d'observation.
- [ ] **Préserver la structure multi-observation lors de l'export** (pas uniquement fusionnée), avec option de fusion configurable.
- [ ] **Supporter entièrement les colonnes BORIS tabulaires avancées**:
  - start/stop/duration/frame/fps
  - colonnes alias documentées BORIS
  - annotation rows enrichies.
- [ ] **Ajouter un validateur d'intégrité BORIS** dédié (state pairs, ordre temporel, overlap states, comportements inconnus).

## 3) Compléter la fidélité CowLog (priorité haute)
- [ ] **Normaliser le profil CowLog “texte résultats”**:
  - en-têtes standard (session/projet/observer/video/fps)
  - annotations métadonnées
  - variantes de séparateurs/tabulations.
- [ ] **Améliorer la reconstruction des états CowLog**:
  - stratégie configurable pour point/start/stop implicites
  - rapport explicite des pertes de fidélité.
- [ ] **Garantir le round-trip CowLog↔PyBehaviorLog↔CowLog** avec mêmes métadonnées clés (dont fps/observer).

## 4) Timecodes et frame-rate (priorité moyenne)
- [ ] **Centraliser un parseur temporel unique** (décimal, ISO8601, SMPTE, frame).
- [ ] **Ajouter la gestion explicite du drop-frame SMPTE** (si nécessaire selon corpus cible).
- [ ] **Rendre la résolution FPS explicite et traçable**:
  - priorité: row > metadata > variable > défaut
  - écrire la source FPS utilisée dans le rapport d'import.

## 5) Rapports et diagnostics (priorité moyenne)
- [ ] **Étendre les rapports de compatibilité** pour lister:
  - champs ignorés
  - conversions appliquées
  - pertes potentielles de fidélité
  - niveau de confiance du parsing.
- [ ] **Ajouter un export “diagnostic JSON”** par import, archivable en CI.

## 6) Tests et certification (priorité haute)
- [ ] **Constituer un corpus de fixtures BORIS/CowLog réels** (versions et variantes récentes).
- [ ] **Ajouter des tests de non-régression paramétrés**:
  - mapping vs list
  - multi-observation
  - timecodes exotiques
  - séparateurs régionaux.
- [ ] **Mettre en place des tests round-trip sémantiques** (pas seulement structurels).
- [ ] **Ajouter un job CI “compatibility certification”** avec seuil de réussite.

## 7) UX / produit (priorité moyenne)
- [ ] **Ajouter un écran de prévisualisation avant import**:
  - format détecté
  - fps détecté
  - nombre d'événements/annotations
  - warnings bloquants/non bloquants.
- [ ] **Permettre à l'utilisateur de corriger manuellement**:
  - fps
  - mapping des colonnes
  - stratégie state reconstruction.

## 8) Documentation (priorité haute)
- [ ] **Mettre à jour la documentation de compatibilité** avec un tableau clair:
  - “supporté totalement”
  - “supporté partiellement”
  - “non supporté”.
- [ ] **Documenter les limites connues** et les chemins recommandés (BORIS JSON vs CowLog texte).
- [ ] **Publier un guide de migration/import** pour laboratoires utilisant BORIS/CowLog.

---

## Plan d'exécution recommandé (ordre)
1. Stabilisation parsing + mode strict/lenient.
2. Fidélité BORIS multi-observation complète.
3. Fidélité CowLog round-trip complète.
4. Diagnostics enrichis et CI de certification.
5. UX de pré-import et documentation finale.

## Critères de fin
- Corpus de référence BORIS/CowLog passe à > 99% d'équivalence sémantique.
- Différences résiduelles documentées automatiquement dans les rapports.
- Pipeline CI bloque toute régression de compatibilité.
