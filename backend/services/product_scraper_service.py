"""
Service Orchestrateur - Gestion des scrapers isolés
"""

import asyncio
from typing import List, Optional
from models import Product
from services.amazon_service import AmazonService
from services.alibaba_service import AlibabaService
from services.walmart_service import WalmartService
from services.cdiscount_service import CdiscountService


class ProductScraperService:
    """
    Service orchestrateur pour les scrapers isolés
    Gère Amazon, Alibaba, Walmart et Cdiscount de manière indépendante
    """
    
    def __init__(self, debug: bool = False):
        self.amazon_service = AmazonService(debug=debug)
        self.alibaba_service = AlibabaService(debug=debug)
        self.walmart_service = WalmartService(debug=True)  # Toujours debug pour Walmart
        self.cdiscount_service = CdiscountService(debug=True)  # Toujours debug pour Cdiscount
        self.debug = debug
        
        if debug:
            print(f"✅ ProductScraperService initialisé")
    
    async def search_products(
        self, 
        keywords: List[str], 
        max_results: int = 20,
        use_amazon: bool = True,
        use_alibaba: bool = True,
        use_walmart: bool = False,
        use_cdiscount: bool = False
    ) -> List[Product]:
        """
        Recherche produits avec sélection STRICTE de sites
        
        Args:
            keywords: Mots-clés de recherche
            max_results: Nombre total de résultats souhaités
            use_amazon: Activer le scraping Amazon
            use_alibaba: Activer le scraping Alibaba
            use_walmart: Activer le scraping Walmart (Firecrawl)
            use_cdiscount: Activer le scraping Cdiscount (Firecrawl)
        
        Returns:
            Liste de produits des sites sélectionnés UNIQUEMENT
        """
        
        search_query = " ".join(keywords)
        
        # Vérification stricte des sélections
        if not use_amazon and not use_alibaba and not use_walmart and not use_cdiscount:
            if self.debug:
                print("❌ Aucun site sélectionné - Arrêt")
            return []
        
        # Affichage des sites sélectionnés
        sites_selected = []
        if use_amazon: sites_selected.append("Amazon")
        if use_alibaba: sites_selected.append("Alibaba")
        if use_walmart: sites_selected.append("Walmart")
        if use_cdiscount: sites_selected.append("Cdiscount")
        
        if self.debug:
            print(f"🔍 Recherche: '{search_query}'")
            print(f"🎯 Sites sélectionnés: {' + '.join(sites_selected)}")
            if not use_amazon:
                print("⏭️ Amazon DÉSACTIVÉ")
            if not use_alibaba:
                print("⏭️ Alibaba DÉSACTIVÉ")
            if not use_walmart:
                print("⏭️ Walmart DÉSACTIVÉ")
            if not use_cdiscount:
                print("⏭️ Cdiscount DÉSACTIVÉ")
        
        # Calculer la répartition des résultats
        active_sites = sum([use_amazon, use_alibaba, use_walmart, use_cdiscount])
        results_per_site = max_results // active_sites
        
        amazon_count = results_per_site if use_amazon else 0
        alibaba_count = results_per_site if use_alibaba else 0
        walmart_count = results_per_site if use_walmart else 0
        cdiscount_count = results_per_site if use_cdiscount else 0
        
        # Distribuer le reste
        remainder = max_results - (amazon_count + alibaba_count + walmart_count + cdiscount_count)
        if remainder > 0 and use_amazon:
            amazon_count += remainder
        
        if self.debug:
            print(f"📊 Répartition:")
            if use_amazon: print(f"   Amazon: {amazon_count}")
            if use_alibaba: print(f"   Alibaba: {alibaba_count}")
            if use_walmart: print(f"   Walmart: {walmart_count}")
            if use_cdiscount: print(f"   Cdiscount: {cdiscount_count}")
        
        # Lancer UNIQUEMENT les scrapers sélectionnés EN PARALLÈLE
        tasks = []
        task_names = []
        
        if self.debug:
            print(f"\n{'='*60}")
            print(f"🚀 LANCEMENT PARALLÈLE DES SCRAPERS")
            print(f"{'='*60}")
        
        # Créer toutes les tâches AVANT de les lancer
        if use_amazon and amazon_count > 0:
            tasks.append(self._scrape_amazon(keywords, amazon_count))
            task_names.append("Amazon")
            if self.debug:
                print(f"� Amazon: {amazon_count} produits demandés")
        
        if use_alibaba and alibaba_count > 0:
            tasks.append(self._scrape_alibaba(keywords, alibaba_count))
            task_names.append("Alibaba")
            if self.debug:
                print(f"� Alibaba: {alibaba_count} produits demandés")
        
        if use_walmart and walmart_count > 0:
            tasks.append(self._scrape_walmart(keywords, walmart_count))
            task_names.append("Walmart")
            if self.debug:
                print(f"� Walmart: {walmart_count} produits demandés")
        
        if use_cdiscount and cdiscount_count > 0:
            tasks.append(self._scrape_cdiscount(keywords, cdiscount_count))
            task_names.append("Cdiscount")
            if self.debug:
                print(f"📦 Cdiscount: {cdiscount_count} produits demandés")
        
        if not tasks:
            if self.debug:
                print("❌ Aucune tâche de scraping à lancer")
            return []
        
        if self.debug:
            print(f"\n⚡ Exécution PARALLÈLE de {len(tasks)} scrapers: {' + '.join(task_names)}")
            print(f"⏱️  Démarrage simultané...")
            import time
            start_time = time.time()
        
        # ⚡ EXÉCUTION PARALLÈLE avec asyncio.gather()
        # Tous les scrapers démarrent AU MÊME INSTANT
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if self.debug:
            elapsed = time.time() - start_time
            print(f"⏱️  Temps total: {elapsed:.2f}s")
            print(f"{'='*60}\n")
        
        # Combiner les résultats avec statistiques détaillées
        all_products = []
        successful_scrapers = []
        failed_scrapers = []
        
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_products.extend(result)
                successful_scrapers.append(task_names[i])
                if self.debug:
                    print(f"✅ [{task_names[i]}] {len(result)} produits récupérés")
            elif isinstance(result, Exception):
                failed_scrapers.append(task_names[i])
                if self.debug:
                    print(f"❌ [{task_names[i]}] Erreur: {result}")
        
        if self.debug:
            print(f"\n{'='*60}")
            print(f"📊 RÉSULTATS DE L'EXÉCUTION PARALLÈLE")
            print(f"{'='*60}")
            print(f"✅ Scrapers réussis: {len(successful_scrapers)}/{len(tasks)}")
            if successful_scrapers:
                print(f"   {', '.join(successful_scrapers)}")
            if failed_scrapers:
                print(f"❌ Scrapers échoués: {len(failed_scrapers)}/{len(tasks)}")
                print(f"   {', '.join(failed_scrapers)}")
            
            # Vérification finale des sources
            sources = {}
            for p in all_products:
                source = p.metadata.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n📦 Produits par source:")
            for source, count in sources.items():
                if source == "amazon":
                    emoji, type_str = "🛒", " (B2C)"
                elif source == "alibaba":
                    emoji, type_str = "🏭", " (B2B)"
                elif source == "walmart":
                    emoji, type_str = "🛍️", " (B2C)"
                elif source == "cdiscount":
                    emoji, type_str = "🛒", " (B2C)"
                else:
                    emoji, type_str = "📦", ""
                print(f"   {emoji} {source.upper()}{type_str}: {count} produits")
            
            # Vérification de conformité
            print(f"\n🔍 Vérification de conformité:")
            conformity_ok = True
            if not use_amazon and "amazon" in sources:
                print("   ⚠️ ERREUR: Produits Amazon trouvés alors qu'Amazon est désactivé!")
                conformity_ok = False
            if not use_alibaba and "alibaba" in sources:
                print("   ⚠️ ERREUR: Produits Alibaba trouvés alors qu'Alibaba est désactivé!")
                conformity_ok = False
            if not use_walmart and "walmart" in sources:
                print("   ⚠️ ERREUR: Produits Walmart trouvés alors que Walmart est désactivé!")
                conformity_ok = False
            if not use_cdiscount and "cdiscount" in sources:
                print("   ⚠️ ERREUR: Produits Cdiscount trouvés alors que Cdiscount est désactivé!")
                conformity_ok = False
            if conformity_ok:
                print("   ✅ Tous les produits proviennent des sources sélectionnées")
            
            print(f"\n✅ TOTAL FINAL: {len(all_products)} produits")
            print(f"{'='*60}\n")
        
        return all_products[:max_results]
    
    async def _scrape_amazon(self, keywords: List[str], max_results: int) -> List[Product]:
        """Scrape Amazon de manière isolée et asynchrone"""
        import time
        start_time = time.time()
        
        try:
            if self.debug:
                print(f"🛒 [Amazon] Démarrage...")
            
            products = await self.amazon_service.search_products(keywords, max_results)
            
            elapsed = time.time() - start_time
            if self.debug:
                print(f"🛒 [Amazon] Terminé en {elapsed:.2f}s: {len(products)} produits")
            
            return products
            
        except Exception as e:
            elapsed = time.time() - start_time
            if self.debug:
                print(f"❌ [Amazon] Erreur après {elapsed:.2f}s: {e}")
            return []
    
    async def _scrape_alibaba(self, keywords: List[str], max_results: int) -> List[Product]:
        """Scrape Alibaba de manière isolée et asynchrone"""
        import time
        start_time = time.time()
        
        try:
            if self.debug:
                print(f"🏭 [Alibaba] Démarrage...")
            
            products = await self.alibaba_service.search_products(keywords, max_results)
            
            elapsed = time.time() - start_time
            if self.debug:
                print(f"🏭 [Alibaba] Terminé en {elapsed:.2f}s: {len(products)} produits")
            
            return products
            
        except Exception as e:
            elapsed = time.time() - start_time
            if self.debug:
                print(f"❌ [Alibaba] Erreur après {elapsed:.2f}s: {e}")
            return []
    
    async def _scrape_walmart(self, keywords: List[str], max_results: int) -> List[Product]:
        """Scrape Walmart de manière isolée et asynchrone avec Firecrawl"""
        import time
        start_time = time.time()
        
        try:
            if self.debug:
                print(f"🛍️ [Walmart] Démarrage...")
            
            products = await self.walmart_service.search_products(keywords, max_results)
            
            elapsed = time.time() - start_time
            if self.debug:
                print(f"�️ [Walmart] Terminé en {elapsed:.2f}s: {len(products)} produits")
            
            return products
            
        except Exception as e:
            elapsed = time.time() - start_time
            if self.debug:
                print(f"❌ [Walmart] Erreur après {elapsed:.2f}s: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    async def _scrape_cdiscount(self, keywords: List[str], max_results: int) -> List[Product]:
        """Scrape Cdiscount de manière isolée et asynchrone avec Firecrawl"""
        import time
        start_time = time.time()
        
        try:
            if self.debug:
                print(f"🛒 [Cdiscount] Démarrage...")
            
            products = await self.cdiscount_service.search_products(keywords, max_results)
            
            elapsed = time.time() - start_time
            if self.debug:
                print(f"🛒 [Cdiscount] Terminé en {elapsed:.2f}s: {len(products)} produits")
            
            return products
            
        except Exception as e:
            elapsed = time.time() - start_time
            if self.debug:
                print(f"❌ [Cdiscount] Erreur après {elapsed:.2f}s: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    async def get_amazon_products_only(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Raccourci pour Amazon uniquement"""
        return await self.search_products(
            keywords=keywords,
            max_results=max_results,
            use_amazon=True,
            use_alibaba=False,
            use_walmart=False
        )
    
    async def get_alibaba_products_only(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Raccourci pour Alibaba uniquement"""
        return await self.search_products(
            keywords=keywords,
            max_results=max_results,
            use_amazon=False,
            use_alibaba=True,
            use_walmart=False
        )
    
    async def get_walmart_products_only(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Raccourci pour Walmart uniquement"""
        return await self.search_products(
            keywords=keywords,
            max_results=max_results,
            use_amazon=False,
            use_alibaba=False,
            use_walmart=True,
            use_cdiscount=False
        )
    
    async def get_cdiscount_products_only(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Raccourci pour Cdiscount uniquement"""
        return await self.search_products(
            keywords=keywords,
            max_results=max_results,
            use_amazon=False,
            use_alibaba=False,
            use_walmart=False,
            use_cdiscount=True
        )