# Documentation API Formulas

## Nouvelles fonctionnalités implémentées

### 1. Récupérer une formule avec ses notes
```http
GET /api/v1/formulas/{formula_id}
```

**Réponse:**
```json
{
  "id": 123,
  "customer_id": 456,
  "file_id": 789,
  "customer_review_id": null,
  "top_notes": [
    {
      "id": 1,
      "name": "Bergamote",
      "quantity": "2",
      "formula_id": 123
    },
    {
      "id": 2,
      "name": "Citron",
      "quantity": "1",
      "formula_id": 123
    }
  ],
  "heart_notes": [
    {
      "id": 3,
      "name": "Rose",
      "quantity": "3",
      "formula_id": 123
    }
  ],
  "base_notes": [
    {
      "id": 4,
      "name": "Musc",
      "quantity": "2 + 1",
      "formula_id": 123
    }
  ]
}
```

---

### 2. Mettre à jour les notes d'une formule
```http
PUT /api/v1/formulas/{formula_id}/notes
```

**Logique:**
- Notes avec `id` → **UPDATE** (modifie la note existante)
- Notes sans `id` → **INSERT** (crée une nouvelle note)
- Notes absentes → **DELETE** (supprime les notes non mentionnées)

**Payload exemple:**
```json
{
  "top_notes": [
    {
      "id": 1,
      "name": "Bergamote",
      "quantity": "3"
    },
    {
      "name": "Orange douce",
      "quantity": "2"
    }
  ],
  "heart_notes": [
    {
      "id": 3,
      "name": "Rose",
      "quantity": "4"
    }
  ],
  "base_notes": []
}
```

**Résultat:**
- Note 1 (Bergamote) → **Mise à jour** de la quantité (2 → 3)
- Note 2 (Citron) → **Supprimée** (absente de la liste)
- Orange douce → **Créée** (pas d'id)
- Note 3 (Rose) → **Mise à jour** de la quantité (3 → 4)
- Note 4 (Musc) → **Supprimée** (base_notes vide)

**Réponse:** Formule complète avec toutes les notes mises à jour

---

### 3. Supprimer une formule et ses notes
```http
DELETE /api/v1/formulas/{formula_id}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Formule 123 et ses notes supprimées avec succès",
  "formula_id": 123
}
```

---

## Cas d'usage Front-End

### Scénario 1: Afficher un customer avec ses formules
```javascript
// 1. Récupérer le customer avec ses formules (déjà implémenté)
const response = await fetch(`/api/v1/customers/${customerId}`)
const customer = await response.json()

// customer.formulas contient déjà toutes les notes
console.log(customer.formulas)
```

### Scénario 2: Modifier les notes d'une formule
```javascript
// L'utilisateur modifie les notes dans le formulaire
const updatedNotes = {
  top_notes: [
    { id: 1, name: "Bergamote", quantity: "3" },  // Modifié
    { name: "Citron vert", quantity: "1" }       // Nouveau
  ],
  heart_notes: [
    { id: 5, name: "Jasmin", quantity: "2" }     // Modifié
  ],
  base_notes: [
    { id: 10, name: "Vanille", quantity: "4" }   // Inchangé
  ]
}

// Envoyer la mise à jour
const response = await fetch(`/api/v1/formulas/${formulaId}/notes`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updatedNotes)
})

const updatedFormula = await response.json()
```

### Scénario 3: Supprimer une formule
```javascript
const response = await fetch(`/api/v1/formulas/${formulaId}`, {
  method: 'DELETE'
})

const result = await response.json()
console.log(result.message) // "Formule X supprimée..."
```

---

## Avantages de cette implémentation

### ✅ Simplicité pour le front
- **Une seule requête** pour mettre à jour toutes les notes
- Pas besoin de gérer manuellement les INSERT/UPDATE/DELETE
- Le backend gère toute la logique de synchronisation

### ✅ Atomicité
- Toute la mise à jour réussit ou échoue ensemble
- Pas d'état incohérent en cas d'erreur partielle

### ✅ Correction automatique intelligente
- **Lors de l'OCR** : Les noms de notes sont automatiquement corrigés via fuzzy matching
  - Exemple: "Bergamot" → "Bergamote"
- **Lors de modifications manuelles** : Aucune correction automatique (l'utilisateur sait ce qu'il fait)
  - L'utilisateur peut écrire "Test" ou "CustomNote" sans que ce soit corrigé

### ✅ Validation
- Pydantic valide automatiquement les payloads
- Messages d'erreur clairs en cas de problème

---

## Tests recommandés

### Test 1: Mise à jour simple
```bash
curl -X PUT http://localhost:8000/api/v1/formulas/1/notes \
  -H "Content-Type: application/json" \
  -d '{
    "top_notes": [
      {"id": 1, "name": "Bergamote", "quantity": "5"}
    ]
  }'
```

### Test 2: Ajout de nouvelles notes
```bash
curl -X PUT http://localhost:8000/api/v1/formulas/1/notes \
  -H "Content-Type: application/json" \
  -d '{
    "top_notes": [
      {"name": "Pamplemousse", "quantity": "2"},
      {"name": "Mandarine", "quantity": "1"}
    ]
  }'
```

### Test 3: Suppression de notes (liste vide)
```bash
curl -X PUT http://localhost:8000/api/v1/formulas/1/notes \
  -H "Content-Type: application/json" \
  -d '{
    "base_notes": []
  }'
```

### Test 4: Suppression de formule
```bash
curl -X DELETE http://localhost:8000/api/v1/formulas/1
```

---

## Structure de la base de données

Les modifications sont compatibles avec votre structure existante:

```
formula
├── id
├── customer_id
├── file_id
└── customer_review_id

top_note / heart_note / base_note
├── id
├── formula_id (FK → formula.id)
├── name
└── quantity
```

**Cascade DELETE:**
Si vous avez configuré `ON DELETE CASCADE` sur les foreign keys, la suppression d'une formule supprimera automatiquement toutes ses notes. Sinon, le code gère manuellement la suppression.

---

## Fichiers modifiés/créés

### CRUD (app/crud/)
- ✅ `crud_formula.py` - Ajout: `get_by_id()`, `delete()`
- ✅ `crud_notes.py` - Ajout: `update_note()`, `delete_note()`, `delete_all_notes_by_formula()`, `get_notes_by_type()`

### Repository (app/repositories/)
- ✅ `formula_repository.py` - Ajout: `get_formula_by_id()`, `delete_formula()`, `update_formula_notes()`

### Schemas (app/schemas/)
- ✅ `formula_schemas.py` - Nouveau fichier avec tous les schémas Pydantic

### Endpoints (app/api/endpoints/)
- ✅ `formulas.py` - Nouveau fichier avec 3 endpoints

### Main (app/)
- ✅ `main.py` - Enregistrement du router `/api/v1/formulas`
