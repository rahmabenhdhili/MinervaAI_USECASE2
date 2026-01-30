# 🤖 Guide de l'IA Explicable (Explainable AI)

## Vue d'ensemble

Le système d'IA explicable fournit des recommandations transparentes et compréhensibles pour aider les utilisateurs à gérer leur budget de courses.

## 🎯 Fonctionnalités Principales

### 1. Analyse du Statut du Budget

**Endpoint:** `GET /api/shopping/cart/budget-status/{session_id}`

**Statuts possibles:**
- ✅ **Safe** (< 75% du budget utilisé)
- ⚡ **Warning** (75-100% du budget utilisé)
  - Low: 75-85%
  - Medium: 85-95%
  - High: 95-100%
- ❌ **Over** (> 100% du budget)

**Exemple de réponse:**
```json
{
  "status": "warning",
  "severity": "high",
  "percentage_used": 95.5,
  "remaining_percentage": 4.5,
  "total": 47.75,
  "budget": 50.00,
  "remaining": 2.25,
  "explanation": "⚠️ **Almost Over Budget!** You've used 95.5% of your budget (47.75 TND out of 50.00 TND). You only have 2.25 TND left. Be very careful with additional items!",
  "recommendations": [
    "You can only add items worth up to 2.25 TND",
    "Avoid adding expensive items",
    "Review your cart for non-essentials"
  ]
}
```

---

### 2. Vérification de l'Impact d'un Article

**Endpoint:** `POST /api/shopping/cart/check-item-impact`

**Paramètres:**
- `session_id`: ID de session
- `product_id`: ID du produit
- `quantity`: Quantité (défaut: 1)

**Cas d'utilisation:**
Avant d'ajouter un article, vérifiez son impact sur le budget.

**Exemple de réponse (Article OK):**
```json
{
  "can_add": true,
  "would_exceed": false,
  "would_warn": false,
  "item_cost": 3.50,
  "new_total": 48.25,
  "new_remaining": 1.75,
  "new_percentage": 96.5,
  "explanation": "✅ **Safe to Add:** Adding 1x Lait Vitalait (3.50 TND) would use 96.5% of your budget. You'd still have 1.75 TND remaining.",
  "suggestion": "This item fits comfortably within your budget."
}
```

**Exemple de réponse (Dépassement):**
```json
{
  "can_add": false,
  "would_exceed": true,
  "would_warn": true,
  "item_cost": 5.00,
  "new_total": 52.75,
  "new_remaining": -2.75,
  "new_percentage": 105.5,
  "explanation": "❌ **Cannot Add:** Adding 1x Huile d'Olive (5.00 TND) would put you 2.75 TND over budget. Your total would be 52.75 TND, exceeding your 50.00 TND budget.",
  "suggestion": "You need to remove 2.75 TND worth of items first, or find a cheaper alternative."
}
```

---

### 3. Analyse Complète du Panier

**Endpoint:** `GET /api/shopping/cart/analysis/{session_id}`

**Retourne:**
- Statut du budget avec explications
- Résumé des achats avec insights
- Statistiques détaillées

**Exemple de réponse:**
```json
{
  "cart": { /* cart object */ },
  "budget_status": {
    "status": "warning",
    "severity": "medium",
    "percentage_used": 87.5,
    "explanation": "⚡ **Approaching Budget Limit!** You've spent 87.5% of your budget...",
    "recommendations": [...]
  },
  "shopping_summary": {
    "message": "Shopping Summary",
    "insights": [
      "You have 8 different products in your cart",
      "Average item price: 5.47 TND",
      "Most expensive item: Huile d'Olive (12.50 TND)",
      "Cheapest item: Pain (0.50 TND)",
      "Shopping from 2 different markets",
      "  • Carrefour: 5 items (30.25 TND)",
      "  • Mazraa Market: 3 items (13.50 TND)"
    ],
    "by_market": {
      "Carrefour": {"count": 5, "total": 30.25},
      "Mazraa Market": {"count": 3, "total": 13.50}
    },
    "statistics": {
      "total_items": 8,
      "total_quantity": 12,
      "average_price": 5.47,
      "most_expensive": {"name": "Huile d'Olive", "price": 12.50},
      "cheapest": {"name": "Pain", "price": 0.50}
    }
  }
}
```

---

### 4. Suggestions d'Optimisation

**Endpoint:** `POST /api/shopping/cart/get-optimization`

**Paramètres:**
- `session_id`: ID de session

**Stratégies proposées:**
1. **Remove** - Supprimer les articles les plus chers
2. **Replace** - Remplacer par des alternatives moins chères
3. **Reduce Quantity** - Réduire les quantités

**Exemple de réponse:**
```json
{
  "budget_status": { /* budget status */ },
  "alternatives": [
    {
      "strategy": "remove",
      "item": "Huile d'Olive Premium",
      "current_price": 12.50,
      "savings": 12.50,
      "explanation": "Remove Huile d'Olive Premium (12.50 TND) - it's your most expensive item. This would save 12.50 TND.",
      "confidence": "high"
    },
    {
      "strategy": "replace",
      "item": "Yaourt Danone",
      "current_price": 3.50,
      "alternative": "Yaourt Vitalait",
      "alternative_price": 2.20,
      "alternative_market": "Mazraa Market",
      "savings": 1.30,
      "explanation": "Replace Yaourt Danone (3.50 TND) with Yaourt Vitalait (2.20 TND) from Mazraa Market. Save 1.30 TND while getting a similar product.",
      "confidence": "medium"
    },
    {
      "strategy": "reduce_quantity",
      "item": "Lait Vitalait",
      "current_quantity": 3,
      "suggested_quantity": 2,
      "savings": 3.50,
      "explanation": "Reduce Lait Vitalait from 3 to 2. Save 3.50 TND. Do you really need that many?",
      "confidence": "medium"
    }
  ],
  "needs_optimization": true
}
```

---

## 🔄 Workflow d'Utilisation

### Scénario 1: Ajout d'Article avec Vérification

```javascript
// 1. Vérifier l'impact avant d'ajouter
const impact = await fetch('/api/shopping/cart/check-item-impact', {
  method: 'POST',
  body: formData
});

// 2. Afficher l'explication à l'utilisateur
if (!impact.can_add) {
  alert(impact.explanation);
  alert(impact.suggestion);
} else if (impact.would_warn) {
  // Afficher un avertissement mais permettre l'ajout
  if (confirm(impact.explanation + "\n\n" + impact.suggestion)) {
    // Ajouter l'article
  }
} else {
  // Ajouter directement
}
```

### Scénario 2: Surveillance Continue du Budget

```javascript
// Après chaque modification du panier
const budgetStatus = await fetch(`/api/shopping/cart/budget-status/${sessionId}`);

// Afficher le statut avec code couleur
if (budgetStatus.status === 'over') {
  showAlert('danger', budgetStatus.explanation);
} else if (budgetStatus.status === 'warning') {
  if (budgetStatus.severity === 'high') {
    showAlert('warning', budgetStatus.explanation);
  } else {
    showAlert('info', budgetStatus.explanation);
  }
} else {
  showAlert('success', budgetStatus.explanation);
}

// Afficher les recommandations
budgetStatus.recommendations.forEach(rec => {
  showRecommendation(rec);
});
```

### Scénario 3: Optimisation du Panier

```javascript
// Quand l'utilisateur dépasse le budget
if (cart.is_over_budget) {
  const optimization = await fetch('/api/shopping/cart/get-optimization', {
    method: 'POST',
    body: formData
  });
  
  // Afficher les suggestions
  optimization.alternatives.forEach(alt => {
    showSuggestion({
      strategy: alt.strategy,
      explanation: alt.explanation,
      savings: alt.savings,
      confidence: alt.confidence
    });
  });
}
```

---

## 📊 Niveaux d'Alerte

### Codes Couleur Recommandés

| Statut | Couleur | Icône | Action |
|--------|---------|-------|--------|
| Safe (< 75%) | 🟢 Vert | ✅ | Aucune action |
| Warning Low (75-85%) | 🟡 Jaune | 💡 | Information |
| Warning Medium (85-95%) | 🟠 Orange | ⚡ | Attention |
| Warning High (95-100%) | 🔴 Rouge clair | ⚠️ | Alerte |
| Over (> 100%) | 🔴 Rouge foncé | ❌ | Blocage |

---

## 💡 Bonnes Pratiques

### 1. Vérification Proactive
```javascript
// Toujours vérifier avant d'ajouter
const canAdd = await checkItemImpact(productId, quantity);
if (!canAdd.can_add) {
  // Proposer des alternatives immédiatement
  const alternatives = await getOptimization();
}
```

### 2. Feedback Continu
```javascript
// Mettre à jour le statut après chaque action
async function updateCart() {
  const analysis = await getCartAnalysis();
  updateBudgetDisplay(analysis.budget_status);
  updateInsights(analysis.shopping_summary);
}
```

### 3. Suggestions Contextuelles
```javascript
// Afficher des suggestions basées sur le contexte
if (budgetStatus.percentage_used > 90) {
  showTip("Vous approchez de votre limite. Considérez des alternatives moins chères.");
} else if (budgetStatus.percentage_used < 50) {
  showTip("Vous avez encore de la marge dans votre budget!");
}
```

---

## 🎨 Exemples d'Interface

### Affichage du Statut du Budget

```jsx
<div className={`budget-status ${status.status}`}>
  <div className="budget-bar">
    <div 
      className="budget-fill" 
      style={{width: `${status.percentage_used}%`}}
    />
  </div>
  <p className="budget-explanation">{status.explanation}</p>
  <ul className="budget-recommendations">
    {status.recommendations.map(rec => (
      <li key={rec}>{rec}</li>
    ))}
  </ul>
</div>
```

### Carte de Suggestion

```jsx
<div className="suggestion-card">
  <div className="suggestion-header">
    <span className="strategy-badge">{alt.strategy}</span>
    <span className="savings">Save {alt.savings} TND</span>
  </div>
  <p className="explanation">{alt.explanation}</p>
  <div className="confidence">
    Confidence: {alt.confidence}
  </div>
  <button onClick={() => applySuggestion(alt)}>
    Apply Suggestion
  </button>
</div>
```

---

## 🔧 Configuration

### Seuils Personnalisables

Dans `explainable_ai_service.py`:

```python
# Modifier les seuils d'alerte
THRESHOLDS = {
    "warning_low": 75,      # 75% du budget
    "warning_medium": 85,   # 85% du budget
    "warning_high": 95,     # 95% du budget
    "over": 100             # 100% du budget
}
```

---

## 📈 Métriques et Insights

Le système fournit automatiquement:
- ✅ Pourcentage du budget utilisé
- ✅ Montant restant
- ✅ Prix moyen par article
- ✅ Article le plus cher
- ✅ Article le moins cher
- ✅ Distribution par marché
- ✅ Nombre total d'articles
- ✅ Quantité totale

---

## 🚀 Intégration Frontend

### React Example

```jsx
import { useState, useEffect } from 'react';

function BudgetMonitor({ sessionId }) {
  const [budgetStatus, setBudgetStatus] = useState(null);
  
  useEffect(() => {
    fetchBudgetStatus();
  }, [sessionId]);
  
  const fetchBudgetStatus = async () => {
    const response = await fetch(
      `/api/shopping/cart/budget-status/${sessionId}`
    );
    const data = await response.json();
    setBudgetStatus(data);
  };
  
  if (!budgetStatus) return <div>Loading...</div>;
  
  return (
    <div className={`budget-monitor ${budgetStatus.status}`}>
      <h3>Budget Status</h3>
      <div className="status-indicator">
        {budgetStatus.status === 'over' && '❌'}
        {budgetStatus.status === 'warning' && '⚠️'}
        {budgetStatus.status === 'safe' && '✅'}
      </div>
      <p>{budgetStatus.explanation}</p>
      <div className="recommendations">
        {budgetStatus.recommendations.map((rec, i) => (
          <div key={i} className="recommendation">{rec}</div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🎯 Résumé

L'IA explicable fournit:
1. ✅ **Transparence** - Explications claires pour chaque recommandation
2. ✅ **Proactivité** - Avertissements avant les problèmes
3. ✅ **Actionabilité** - Suggestions concrètes et applicables
4. ✅ **Contexte** - Insights basés sur le comportement d'achat
5. ✅ **Confiance** - Niveaux de confiance pour chaque suggestion

**Résultat:** Une expérience d'achat plus intelligente et transparente! 🎉
