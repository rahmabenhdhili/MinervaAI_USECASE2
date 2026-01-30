# Guide de Chargement Qdrant

Ce guide explique comment charger vos produits dans Qdrant de différentes manières.

## 📋 Options de Chargement

### Option 1: Charger TOUS les produits (Réinitialisation complète)
```bash
python load_db_to_qdrant.py
```
**Quand l'utiliser:**
- Première fois que vous configurez Qdrant
- Vous voulez réinitialiser complètement la collection
- Vous avez modifié le modèle d'embedding

**⚠️ Attention:** Supprime et recrée la collection complète

---

### Option 2: Charger uniquement les produits récents (Recommandé)
```bash
# Charger les produits des dernières 24 heures
python load_recent_to_qdrant.py

# Charger les produits des dernières 48 heures
python load_recent_to_qdrant.py --hours 48

# Charger les produits de la dernière semaine
python load_recent_to_qdrant.py --hours 168
```
**Quand l'utiliser:**
- Après avoir scrapé de nouveaux produits
- Mise à jour incrémentale (plus rapide)
- Vous voulez ajouter sans supprimer l'existant

**✅ Avantages:**
- Rapide (traite uniquement les nouveaux produits)
- Conserve les produits existants
- Pas de downtime

---

### Option 3: Charger tous les produits Carrefour
```bash
python load_carrefour_to_qdrant.py
```
**Quand l'utiliser:**
- Après avoir scrapé Carrefour avec `scrape_carrefour_config.py`
- Vous voulez ajouter tous les produits Carrefour d'un coup

---

### Option 4: Charger tous les produits d'un marché spécifique
```bash
# Charger tous les produits Carrefour
python load_recent_to_qdrant.py --market "Carrefour"

# Charger tous les produits Mazraa Market
python load_recent_to_qdrant.py --market "Mazraa Market"

# Charger tous les produits Aziza
python load_recent_to_qdrant.py --market "Aziza"
```

---

## 🔄 Workflow Recommandé

### Après avoir scrapé de nouveaux produits Carrefour:

1. **Scraper les produits:**
   ```bash
   python scrape_carrefour_config.py
   ```

2. **Vérifier les produits ajoutés:**
   ```bash
   python browse_database.py
   ```

3. **Charger dans Qdrant (choisir une option):**
   
   **Option A - Rapide (dernières 24h):**
   ```bash
   python load_recent_to_qdrant.py
   ```
   
   **Option B - Tous les Carrefour:**
   ```bash
   python load_carrefour_to_qdrant.py
   ```
   
   **Option C - Réinitialisation complète:**
   ```bash
   python load_db_to_qdrant.py
   ```

---

## 📊 Vérifier le Chargement

### Vérifier combien de produits sont dans Qdrant:
```bash
python diagnose_qdrant.py
```

### Vérifier les produits dans la base de données:
```bash
python browse_database.py
```

---

## 💡 Conseils

### Quand utiliser chaque méthode:

| Situation | Méthode Recommandée | Commande |
|-----------|-------------------|----------|
| Première installation | Chargement complet | `python load_db_to_qdrant.py` |
| Après scraping Carrefour | Produits récents | `python load_recent_to_qdrant.py` |
| Après scraping (24h) | Produits récents | `python load_recent_to_qdrant.py` |
| Après scraping (plusieurs jours) | Par marché | `python load_recent_to_qdrant.py --market "Carrefour"` |
| Problème avec Qdrant | Réinitialisation | `python load_db_to_qdrant.py` |

### Performance:

- **Chargement complet** (1000 produits): ~5-10 minutes
- **Chargement incrémental** (100 produits): ~30-60 secondes
- **Chargement par marché** (500 produits): ~2-5 minutes

---

## 🐛 Dépannage

### "No new products found"
```bash
# Vérifier les produits dans la DB
python browse_database.py

# Augmenter la fenêtre de temps
python load_recent_to_qdrant.py --hours 168  # 1 semaine
```

### "Collection doesn't exist"
Le script créera automatiquement la collection. Pas d'action nécessaire.

### "Out of memory"
```bash
# Charger par petits lots
python load_recent_to_qdrant.py --hours 12  # Plus petit lot
```

---

## 📝 Exemples Complets

### Exemple 1: Workflow complet Carrefour
```bash
# 1. Scraper Carrefour
python scrape_carrefour_config.py

# 2. Vérifier (optionnel)
python browse_database.py

# 3. Charger dans Qdrant
python load_carrefour_to_qdrant.py

# 4. Vérifier Qdrant
python diagnose_qdrant.py
```

### Exemple 2: Mise à jour quotidienne
```bash
# Charger les produits des dernières 24h
python load_recent_to_qdrant.py

# Vérifier
python diagnose_qdrant.py
```

### Exemple 3: Réinitialisation complète
```bash
# Supprimer et recréer tout
python load_db_to_qdrant.py

# Vérifier
python diagnose_qdrant.py
```

---

## 🎯 Résumé Rapide

**Pour la plupart des cas (après scraping):**
```bash
python load_recent_to_qdrant.py
```

**Pour charger tous les Carrefour:**
```bash
python load_carrefour_to_qdrant.py
```

**Pour tout réinitialiser:**
```bash
python load_db_to_qdrant.py
```
