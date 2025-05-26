# linkedin_scraper_enhanced.py
import time
import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging
import random
from urllib.parse import urlencode, urlparse, parse_qs

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    """
    Scraper avancé pour les offres d'emploi LinkedIn avec stockage en MongoDB
    """
    
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017", db_name: str = "linkedin_scraper"):
        self.mongodb_uri = mongodb_uri
        self.db_name = db_name
        self.driver = None
        self.db = None
        self.client = None
        
        # Configuration des sélecteurs CSS (mis à jour)
        self.selectors = {
            'job_cards': [
                "div[data-job-id]",
                ".job-search-card",
                ".base-card",
                "li[data-occludable-job-id]"
            ],
            'title': [
                "h3.base-search-card__title a",
                ".job-search-card__title a",
                "h4.job-search-card__title",
                "a[data-control-name='job_search_job_title']"
            ],
            'company': [
                "h4.base-search-card__subtitle a",
                ".job-search-card__company-name",
                "a[data-control-name='job_search_company_name']"
            ],
            'location': [
                "span.job-search-card__location",
                ".base-search-card__location"
            ],
            'time_posted': [
                "time.job-search-card__listdate",
                ".job-search-card__listdate--new"
            ],
            'description': [
                "div.show-more-less-html__markup",
                ".jobs-description__content",
                ".job-details-description"
            ]
        }
        
        # URLs de base pour différents types de recherche
        self.base_urls = {
            'jobs': 'https://www.linkedin.com/jobs/search/?',
            'public_jobs': 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?'
        }
        
    async def initialize_database(self):
        """Initialise la connexion à MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client[self.db_name]
            
            # Test de la connexion
            await self.db.admin.command('ping')
            logger.info("✅ Connexion MongoDB établie avec succès")
            
            # Création des index si nécessaire
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion MongoDB: {e}")
            raise
    
    async def _create_indexes(self):
        """Crée les index nécessaires pour optimiser les performances"""
        try:
            # Index pour éviter les doublons
            await self.db.jobs.create_index([
                ("title", 1),
                ("company", 1),
                ("location", 1)
            ], unique=True, background=True)
            
            # Index pour les recherches
            await self.db.jobs.create_index("createdAt", background=True)
            await self.db.jobs.create_index("status", background=True)
            await self.db.jobs.create_index("postedAt", background=True)
            
            logger.info("✅ Index MongoDB créés")
        except Exception as e:
            logger.warning(f"⚠️ Erreur création index: {e}")
    
    def setup_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Configure et retourne une instance de Chrome WebDriver"""
        options = Options()
        
        if headless:
            options.add_argument("--headless")
        
        # Configuration anti-détection
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent aléatoire
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"❌ Erreur initialisation WebDriver: {e}")
            raise
    
    def build_search_url(self, 
                        keywords: Optional[List[str]] = None,
                        location: Optional[str] = None,
                        experience_level: Optional[str] = None,
                        job_type: Optional[str] = None,
                        date_posted: Optional[str] = None,
                        salary_range: Optional[str] = None,
                        company_size: Optional[str] = None,
                        sort_by: str = "DD",  # Date Descending
                        start: int = 0) -> str:
        """Construit l'URL de recherche LinkedIn avec les filtres spécifiés"""
        
        params = {
            'start': start,
            'sortBy': sort_by
        }
        
        if keywords:
            params['keywords'] = ' '.join(keywords)
        
        if location:
            params['location'] = location
        
        # Filtres d'expérience
        experience_filters = {
            'internship': 'f_E=1',
            'entry': 'f_E=2', 
            'associate': 'f_E=3',
            'mid_senior': 'f_E=4',
            'director': 'f_E=5',
            'executive': 'f_E=6'
        }
        if experience_level and experience_level in experience_filters:
            params.update(dict(pair.split('=') for pair in experience_filters[experience_level].split('&')))
        
        # Types d'emploi
        job_type_filters = {
            'full_time': 'f_JT=F',
            'part_time': 'f_JT=P', 
            'contract': 'f_JT=C',
            'temporary': 'f_JT=T',
            'internship': 'f_JT=I',
            'volunteer': 'f_JT=V'
        }
        if job_type and job_type in job_type_filters:
            params.update(dict(pair.split('=') for pair in job_type_filters[job_type].split('&')))
        
        # Date de publication
        date_filters = {
            'past_24h': 'f_TPR=r86400',
            'past_week': 'f_TPR=r604800',
            'past_month': 'f_TPR=r2592000'
        }
        if date_posted and date_posted in date_filters:
            params.update(dict(pair.split('=') for pair in date_filters[date_posted].split('&')))
        
        return self.base_urls['jobs'] + urlencode(params)
    
    def extract_job_data(self, job_element, page_source: str = None) -> Optional[Dict[str, Any]]:
        """Extrait les données d'une offre d'emploi à partir d'un élément HTML"""
        try:
            job_data = {
                'scraped_at': datetime.utcnow(),
                'status': 'active',
                'source': 'linkedin'
            }
            
            # Extraction du titre
            title = self._extract_with_selectors(job_element, self.selectors['title'])
            if not title:
                return None
            job_data['title'] = title
            
            # Extraction de l'entreprise
            company = self._extract_with_selectors(job_element, self.selectors['company'])
            if company:
                job_data['company'] = company
            
            # Extraction de la localisation
            location = self._extract_with_selectors(job_element, self.selectors['location'])
            if location:
                job_data['location'] = location
            
            # Extraction de la date de publication
            time_posted = self._extract_with_selectors(job_element, self.selectors['time_posted'], attr='datetime')
            if time_posted:
                job_data['posted_at'] = self._parse_linkedin_date(time_posted)
            
            # Extraction du lien
            link_element = job_element.find('a')
            if link_element and link_element.has_attr('href'):
                job_data['linkedin_url'] = link_element['href']
                job_data['job_id'] = self._extract_job_id(link_element['href'])
            
            # Extraction des informations supplémentaires
            job_data.update({
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow(),
                'views': 0,
                'applications': 0,
                'remote': self._detect_remote_work(title + ' ' + (location or '')),
                'urgent': self._detect_urgent(title),
                'description': '',  # Sera rempli lors du scraping détaillé
                'requirements': [],
                'benefits': [],
                'salary': None
            })
            
            return job_data
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction données job: {e}")
            return None
    
    def _extract_with_selectors(self, element, selectors: List[str], attr: str = None) -> Optional[str]:
        """Extrait du texte en essayant plusieurs sélecteurs CSS"""
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found:
                    if attr:
                        return found.get(attr, '').strip()
                    return found.get_text(strip=True)
            except:
                continue
        return None
    
    def _extract_job_id(self, url: str) -> Optional[str]:
        """Extrait l'ID du job à partir de l'URL LinkedIn"""
        try:
            # Patterns courants pour les IDs LinkedIn
            patterns = [
                r'/jobs/view/(\d+)',
                r'currentJobId=(\d+)',
                r'jobId=(\d+)',
                r'-(\d+)(?:\?|$)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            return None
        except:
            return None
    
    def _parse_linkedin_date(self, date_str: str) -> Optional[datetime]:
        """Parse les différents formats de date LinkedIn"""
        try:
            # Format ISO
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Formats relatifs
            now = datetime.utcnow()
            
            if 'minute' in date_str:
                minutes = int(re.search(r'(\d+)', date_str).group(1))
                return now - timedelta(minutes=minutes)
            elif 'hour' in date_str or 'heure' in date_str:
                hours = int(re.search(r'(\d+)', date_str).group(1))
                return now - timedelta(hours=hours)
            elif 'day' in date_str or 'jour' in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                return now - timedelta(days=days)
            elif 'week' in date_str or 'semaine' in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                return now - timedelta(weeks=weeks)
            elif 'month' in date_str or 'mois' in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                return now - timedelta(days=months*30)
            
            return now
        except:
            return datetime.utcnow()
    
    def _detect_remote_work(self, text: str) -> bool:
        """Détecte si le poste permet le télétravail"""
        remote_keywords = [
            'remote', 'télétravail', 'home office', 'work from home',
            'distributed', 'anywhere', 'telecommute', 'virtual'
        ]
        return any(keyword in text.lower() for keyword in remote_keywords)
    
    def _detect_urgent(self, text: str) -> bool:
        """Détecte si le poste est urgent"""
        urgent_keywords = [
            'urgent', 'asap', 'immediately', 'immédiat',
            'quickly', 'fast', 'emergency', 'prioritaire'
        ]
        return any(keyword in text.lower() for keyword in urgent_keywords)
    
    async def scrape_jobs(self,
                         keywords: Optional[List[str]] = None,
                         location: Optional[str] = None,
                         max_pages: int = 5,
                         delay_range: tuple = (2, 5),
                         **filters) -> List[Dict[str, Any]]:
        """
        Scrape les offres d'emploi LinkedIn avec les paramètres spécifiés
        
        Args:
            keywords: Liste de mots-clés pour la recherche
            location: Localisation
            max_pages: Nombre maximum de pages à scraper
            delay_range: Délai aléatoire entre les requêtes (min, max)
            **filters: Filtres additionnels (experience_level, job_type, etc.)
        
        Returns:
            Liste des offres d'emploi extraites
        """
        if not self.db:
            await self.initialize_database()
        
        all_jobs = []
        
        try:
            self.driver = self.setup_driver(headless=True)
            logger.info(f"🚀 Début du scraping - Max {max_pages} pages")
            
            for page in range(max_pages):
                start = page * 25
                url = self.build_search_url(
                    keywords=keywords,
                    location=location,
                    start=start,
                    **filters
                )
                
                logger.info(f"📄 Scraping page {page + 1}: {start} résultats")
                
                try:
                    # Navigation vers la page
                    self.driver.get(url)
                    
                    # Attente du chargement
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "main"))
                    )
                    
                    # Scroll progressif pour charger le contenu dynamique
                    await self._progressive_scroll(self.driver)
                    
                    # Extraction des données
                    page_jobs = await self._extract_jobs_from_page(self.driver.page_source)
                    
                    if not page_jobs:
                        logger.warning(f"⚠️ Aucun job trouvé page {page + 1}")
                        break
                    
                    all_jobs.extend(page_jobs)
                    logger.info(f"✅ Page {page + 1}: {len(page_jobs)} jobs extraits")
                    
                    # Délai aléatoire anti-détection
                    delay = random.uniform(*delay_range)
                    logger.info(f"⏱️ Pause de {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    
                except TimeoutException:
                    logger.error(f"❌ Timeout page {page + 1}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Erreur page {page + 1}: {e}")
                    continue
            
            # Sauvegarde en base de données
            if all_jobs:
                saved_count = await self._save_jobs_to_db(all_jobs)
                logger.info(f"💾 {saved_count}/{len(all_jobs)} jobs sauvegardés en base")
            
            return all_jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur générale scraping: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔄 Driver fermé")
    
    async def _progressive_scroll(self, driver, max_scrolls: int = 3):
        """Effectue un scroll progressif pour charger le contenu dynamique"""
        for i in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)
            
            # Vérification si de nouveaux éléments sont chargés
            current_height = driver.execute_script("return document.body.scrollHeight")
            await asyncio.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if current_height == new_height:
                break
    
    async def _extract_jobs_from_page(self, page_source: str) -> List[Dict[str, Any]]:
        """Extrait tous les jobs d'une page HTML"""
        soup = BeautifulSoup(page_source, 'html.parser')
        jobs = []
        
        # Essai avec différents sélecteurs
        for selector in self.selectors['job_cards']:
            job_elements = soup.select(selector)
            if job_elements:
                break
        
        if not job_elements:
            logger.warning("⚠️ Aucun élément job trouvé avec les sélecteurs actuels")
            return []
        
        for element in job_elements:
            job_data = self.extract_job_data(element)
            if job_data:
                jobs.append(job_data)
        
        return jobs
    
    async def _save_jobs_to_db(self, jobs: List[Dict[str, Any]]) -> int:
        """Sauvegarde les jobs en base avec gestion des doublons"""
        saved_count = 0
        
        for job in jobs:
            try:
                # Tentative d'insertion avec gestion des doublons
                result = await self.db.jobs.replace_one(
                    {
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location']
                    },
                    job,
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde job: {e}")
                continue
        
        return saved_count
    
    async def get_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails complets d'une offre d'emploi"""
        if not self.driver:
            self.driver = self.setup_driver()
        
        try:
            self.driver.get(job_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {
                'description': '',
                'requirements': [],
                'benefits': [],
                'company_info': {},
                'salary': None
            }
            
            # Description détaillée
            desc_element = soup.select_one('div.show-more-less-html__markup')
            if desc_element:
                details['description'] = desc_element.get_text(strip=True)
                
                # Extraction des exigences et avantages
                details['requirements'] = self._extract_requirements(details['description'])
                details['benefits'] = self._extract_benefits(details['description'])
            
            # Informations sur l'entreprise
            company_element = soup.select_one('.job-details-company-modules')
            if company_element:
                details['company_info'] = self._extract_company_info(company_element)
            
            return details
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction détails: {e}")
            return None
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extrait les exigences à partir de la description"""
        requirements = []
        
        # Patterns pour identifier les exigences
        requirement_patterns = [
            r'required?:?\s*(.+?)(?:\n|$)',
            r'must have:?\s*(.+?)(?:\n|$)',
            r'qualifications?:?\s*(.+?)(?:\n|$)',
            r'experience:?\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                req_text = match.group(1).strip()
                if len(req_text) > 10 and len(req_text) < 200:
                    requirements.append(req_text)
        
        return requirements[:10]  # Limite à 10 exigences
    
    def _extract_benefits(self, description: str) -> List[str]:
        """Extrait les avantages à partir de la description"""
        benefits = []
        
        benefit_keywords = [
            'health insurance', 'assurance santé', '401k', 'vacation',
            'remote work', 'flexible hours', 'bonus', 'stock options',
            'formation', 'training', 'development', 'congés'
        ]
        
        sentences = re.split(r'[.!?]', description)
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in benefit_keywords):
                cleaned = sentence.strip()
                if 20 < len(cleaned) < 150:
                    benefits.append(cleaned)
        
        return benefits[:5]  # Limite à 5 avantages
    
    def _extract_company_info(self, company_element) -> Dict[str, str]:
        """Extrait les informations sur l'entreprise"""
        info = {}
        
        try:
            # Taille de l'entreprise
            size_element = company_element.select_one('.job-details-company-modules__company-size')
            if size_element:
                info['size'] = size_element.get_text(strip=True)
            
            # Secteur d'activité
            industry_element = company_element.select_one('.job-details-company-modules__industry')
            if industry_element:
                info['industry'] = industry_element.get_text(strip=True)
            
            # Site web
            website_element = company_element.select_one('a[href^="http"]')
            if website_element:
                info['website'] = website_element.get('href')
        
        except Exception as e:
            logger.error(f"❌ Erreur extraction info entreprise: {e}")
        
        return info
    
    async def close(self):
        """Ferme les connexions"""
        if self.driver:
            self.driver.quit()
        if self.client:
            self.client.close()
        logger.info("🔄 Connexions fermées")

# Fonction utilitaire pour utilisation standalone
async def scrape_linkedin_jobs(
    keywords: List[str] = None,
    location: str = None,
    max_pages: int = 3,
    mongodb_uri: str = "mongodb://localhost:27017",
    db_name: str = "linkedin_scraper",
    **filters
) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour scraper LinkedIn facilement
    
    Exemple d'utilisation:
    jobs = await scrape_linkedin_jobs(
        keywords=['python', 'developer'],
        location='Paris, France',
        max_pages=2,
        experience_level='mid_senior',
        job_type='full_time'
    )
    """
    scraper = LinkedInJobScraper(mongodb_uri, db_name)
    
    try:
        jobs = await scraper.scrape_jobs(
            keywords=keywords,
            location=location,
            max_pages=max_pages,
            **filters
        )
        return jobs
    finally:
        await scraper.close()

# Script d'exemple pour tests
if __name__ == "__main__":
    async def main():
        # Configuration du scraping
        config = {
            'keywords': ['développeur', 'python'],
            'location': 'Paris, France',
            'max_pages': 2,
            'experience_level': 'mid_senior',
            'job_type': 'full_time',
            'date_posted': 'past_week'
        }
        
        print("🚀 Démarrage du scraping LinkedIn...")
        jobs = await scrape_linkedin_jobs(**config)
        
        print(f"✅ Scraping terminé: {len(jobs)} offres collectées")
        
        # Affichage d'un échantillon
        for i, job in enumerate(jobs[:3]):
            print(f"\n--- Offre {i+1} ---")
            print(f"Titre: {job.get('title', 'N/A')}")
            print(f"Entreprise: {job.get('company', 'N/A')}")
            print(f"Lieu: {job.get('location', 'N/A')}")
            print(f"Remote: {job.get('remote', False)}")
    
    # Exécution
    asyncio.run(main())