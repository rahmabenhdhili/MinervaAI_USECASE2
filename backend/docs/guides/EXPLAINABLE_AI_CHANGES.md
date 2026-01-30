# 🤖 Explainable AI - Changements Implémentés

## ✅ Problèmes Résolus

### 1. ❌ "No products found" pour Aziza
**Problème:** Le mapping du marché ne correspondait pas
- Frontend: `"aziza"`
- Database: `"aziza"` (minuscule)
- Mapping API: `"Aziza"` (majuscule) ❌

**Solution:** Corrigé le mapping dans `backend/app/api/shopping.py`
```python
MARKET_MAPPING = {
    "aziza": "aziza",  # Match database exactly
}
```

### 2. ✅ Suppression de "AI Suggested Quantity"
**Changement:** Retiré la section de suggestion automatique de quantité
- Fichier: `frontend/src/ShoppingMode.jsx`
- Lignes supprimées: Section complète avec Package icon
- Raison: Simplification de l'interface utilisateur

---

## 🎯 Nouveau Service: Explainable AI

### Fichier Créé: `backend/app/services/explainable_ai_service.py`

### Fonctionnalités Principales

#### 1. **Analyse du Statut Budget** (`analyze_budget_status`)
Retourne:
```python
{
    "status": "safe" | "warning" | "over",
    "severity": "none" | "low" | "medium" | "high" | "critical",
    "percentage_used": 75.5,
    "remaining_percentage": 24.5,
    "explanation": "⚠️ Budget Alert: You've used 75.5% of your budget...",
    "recommendations": [
        "You have 12.25 TND left to spend",
        "You're doing well, but keep an eye on your spending"
    ]
}
```

**Niveaux d'Alerte:**
- ✅ **Safe** (< 75%): "Within Budget"
- ⚡ **Warning Low** (75-85%): "Budget Alert"
- ⚡ **Warning Medium** (85-95%): "Approaching Budget Limit"
- ⚠️ **Warning High** (95-100%): "Almost Over Budget"
- ❌ **Over** (> 100%): "Budget Exceeded"

#### 2. **Impact d'Ajout d'Article** (`explain_item_impact`)
Avant d'ajouter un article, explique:
```python
{
    "can_add": true,
    "would_exceed": false,
    "would_warn": true,
    "item_cost": 5.50,
    "new_total": 45.50,
    "new_remaining": 4.50,
    "new_percentage": 91.0,
    "explanation": "⚠️ Budget Warning: Adding 2x Milk (5.50 TND) would use 91% of your budget...",
    "suggestion": "Consider if this item is essential before adding it."
}
```

#### 3. **Alternatives Intelligentes** (`get_smart_alternatives`)
Suggère des alternatives avec explications claires:
```python
[
    {
        "strategy": "remove",
        "item": "Expensive Product",
        "savings": 15.50,
        "explanation": "Remove Expensive Product (15.50 TND) - it's your most expensive item...",
        "confidence": "high"
    },
    {
        "strategy": "replace",
        "item": "Brand A Milk",
        "alternative": "Brand B Milk",
        "alternative_price": 3.20,
        "savings": 2.30,
        "explanation": "Replace Brand A Milk (5.50 TND) with Brand B Milk (3.20 TND)...",
        "confidence": "medium"
    },
    {
        "strategy": "reduce_quantity",
        "item": "Yogurt",
        "current_quantity": 3,
        "suggested_quantity": 2,
        "savings": 2.50,
        "explanation": "Reduce Yogurt from 3 to 2. Save 2.50 TND...",
        "confidence": "medium"
    }
]
```

#### 4. **Résumé Shopping** (`generate_shopping_summary`)
Insights sur le panier:
```python
{
    "insights": [
        "You have 5 different products in your cart",
        "Average item price: 8.50 TND",
        "Most expensive item: Premium Coffee (25.00 TND)",
        "Shopping from 2 different markets"
    ],
    "by_market": {
        "Carrefour": {"count": 3, "total": 30.50},
        "Mazraa Market": {"count": 2, "total": 12.00}
    }
}
```

---

## 🔌 Nouveaux Endpoints API

### 1. GET `/api/shopping/cart/analysis/{session_id}`
Analyse complète du panier avec insights

**Réponse:**
```json
{
    "cart": {...},
    "budget_status": {
        "status": "warning",
        "explanation": "⚠️ Budget Alert...",
        "recommendations": [...]
    },
    "shopping_summary": {
        "insights": [...],
        "statistics": {...}
    }
}
```

### 2. POST `/api/shopping/cart/check-item-impact`
Vérifie l'impact avant d'ajouter un article

**Paramètres:**
- `session_id`: ID de session
- `product_id`: ID du produit
- `quantity`: Quantité (défaut: 1)

**Réponse:**
```json
{
    "can_add": true,
    "explanation": "✅ Safe to Add: Adding 1x Milk...",
    "suggestion": "This item fits comfortably within your budget.",
    "new_total": 45.50,
    "new_percentage": 91.0
}
```

### 3. POST `/api/shopping/cart/get-optimization`
Suggestions d'optimisation avec IA

**Paramètres:**
- `session_id`: ID de session

**Réponse:**
```json
{
    "budget_status": {...},
    "alternatives": [
        {
            "strategy": "remove",
            "explanation": "Remove most expensive item...",
            "savings": 15.50
        }
    ],
    "needs_optimization": true
}
```

### 4. GET `/api/shopping/cart/budget-status/{session_id}`
Statut budget détaillé

**Réponse:**
```json
{
    "status": "warning",
    "severity": "medium",
    "percentage_used": 85.5,
    "explanation": "⚡ Approaching Budget Limit!...",
    "recommendations": [
        "You have 7.25 TND left for additional items",
        "Be selective with remaining purchases"
    ]
}
```

---

## 🔄 Modifications du Service Cart

### Méthode `add_item` Améliorée
Maintenant retourne:
```python
{
    "cart": VirtualCart,
    "budget_status": {...},  # Nouveau!
    "item_added": {...},
    "impact_analysis": {...}  # Nouveau!
}
```

### Nouvelles Méthodes
1. `get_cart_analysis(session_id)` - Analyse complète
2. `get_optimization_suggestions(session_id, all_products)` - Suggestions IA

---

## 💡 Exemples d'Utilisation

### Frontend - Vérifier avant d'ajouter
```javascript
// Avant d'ajouter au panier
const impact = await fetch('/api/shopping/cart/check-item-impact', {
    method: 'POST',
    body: formData
});

if (!impact.can_add) {
    alert(impact.explanation);
    // Montrer les suggestions
}
```

### Frontend - Afficher le statut budget
```javascript
const status = await fetch(`/api/shopping/cart/budget-status/${sessionId}`);

// Afficher avec couleurs selon severity
if (status.status === 'over') {
    // Rouge - Critique
} else if (status.severity === 'high') {
    // Orange - Attention
} else if (status.severity === 'medium') {
    // Jaune - Avertissement
}
```

### Frontend - Obtenir des suggestions
```javascript
const optimization = await fetch('/api/shopping/cart/get-optimization', {
    method: 'POST',
    body: formData
});

// Afficher les alternatives
optimization.alternatives.forEach(alt => {
    console.log(alt.explanation);
    console.log(`Save: ${alt.savings} TND`);
});
```

---

## 📊 Avantages de l'IA Explicable

### Transparence
- ✅ Explications claires en langage naturel
- ✅ Raisons pour chaque recommandation
- ✅ Niveau de confiance pour chaque suggestion

### Proactivité
- ⚡ Avertissements avant dépassement
- ⚡ Suggestions avant problèmes
- ⚡ Analyse en temps réel

### Aide à la Décision
- 💡 Alternatives concrètes
- 💡 Économies calculées
- 💡 Impact prévisualisé

---

## 🎨 Intégration Frontend Recommandée

### 1. Badge de Statut Budget
```jsx
<div className={`badge ${budgetStatus.severity}`}>
    {budgetStatus.percentage_used}% utilisé
</div>
```

### 2. Tooltip sur Ajout
```jsx
<button onClick={checkImpact}>
    Ajouter au panier
    {impact && !impact.can_add && (
        <Tooltip>{impact.explanation}</Tooltip>
    )}
</button>
```

### 3. Section Suggestions
```jsx
{alternatives.map(alt => (
    <div className="suggestion-card">
        <h4>{alt.strategy}</h4>
        <p>{alt.explanation}</p>
        <span className="savings">💰 {alt.savings} TND</span>
    </div>
))}
```

---

## 🚀 Prochaines Étapes

1. ✅ Service Explainable AI créé
2. ✅ Endpoints API ajoutés
3. ✅ Service Cart mis à jour
4. ✅ Bug Aziza corrigé
5. ✅ AI Suggested Quantity supprimé
6. 🔄 Intégrer dans le frontend (à faire)
7. 🔄 Tester avec vrais utilisateurs
8. 🔄 Affiner les explications selon feedback

---

## 📝 Notes Techniques

### Performance
- Calculs en temps réel (< 100ms)
- Pas d'appel LLM pour analyse basique
- LLM utilisé uniquement pour suggestions complexes

### Scalabilité
- Service stateless
- Peut être mis en cache
- Compatible avec Redis

### Maintenance
- Code modulaire et testable
- Explications facilement modifiables
- Seuils configurables
