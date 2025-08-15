#!/usr/bin/env python3
"""
Script corrigé pour scraper Medium avec gestion automatique de ChromeDriver sur macOS ARM64
"""

import csv
import time
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re
from datetime import datetime

def setup_driver():
    """Configure le driver Chrome avec gestion automatique de ChromeDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Gestion spéciale pour macOS ARM64
    if platform.machine() == 'arm64':
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Installation automatique de ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erreur avec ChromeDriver automatique : {e}")
        print("Tentative avec ChromeDriver manuel...")
        
        # Essayer de trouver ChromeDriver dans le PATH
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"Erreur avec ChromeDriver manuel : {e2}")
            print("Veuillez installer ChromeDriver manuellement :")
            print("brew install --cask chromedriver")
            raise e2

def scroll_to_bottom(driver, max_scrolls=100):
    """Fait défiler la page jusqu'en bas pour charger tous les articles"""
    print("Défilement de la page pour charger tous les articles...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    no_change_count = 0
    
    while scroll_count < max_scrolls:
        # Faire défiler jusqu'en bas
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Attendre que la page se charge
        time.sleep(3)
        
        # Calculer la nouvelle hauteur
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Si la hauteur n'a pas changé
        if new_height == last_height:
            no_change_count += 1
            if no_change_count >= 3:  # 3 tentatives sans changement
                print("Fin de la page atteinte")
                break
        else:
            no_change_count = 0
            
        last_height = new_height
        scroll_count += 1
        print(f"Défilement {scroll_count}/{max_scrolls}")
    
    # Remonter en haut
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

def extract_articles(driver):
    """Extrait tous les articles de la page Medium"""
    print("Extraction des articles...")
    
    # Attendre que les articles se chargent
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article, [data-testid='article']"))
        )
    except TimeoutException:
        print("Aucun article trouvé avec le sélecteur principal")
        # Essayer d'autres sélecteurs
        pass
    
    # Essayer différents sélecteurs pour les articles
    selectors = [
        "article",
        "[data-testid='article']",
        ".postArticle",
        ".streamItem",
        "[class*='article']",
        "[class*='post']"
    ]
    
    articles = []
    for selector in selectors:
        try:
            articles = driver.find_elements(By.CSS_SELECTOR, selector)
            if articles:
                print(f"Articles trouvés avec le sélecteur '{selector}': {len(articles)}")
                break
        except:
            continue
    
    if not articles:
        print("Aucun article trouvé avec aucun sélecteur")
        return []
    
    extracted_articles = []
    
    for article in articles:
        try:
            # Extraire le titre avec différents sélecteurs
            title = None
            title_selectors = ["h2", "h3", "h4", "[class*='title']", "[class*='headline']"]
            for title_selector in title_selectors:
                try:
                    title_element = article.find_element(By.CSS_SELECTOR, title_selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except:
                    continue
            
            # Extraire l'URL
            url = None
            try:
                link_element = article.find_element(By.CSS_SELECTOR, "a[href*='medium.com']")
                url = link_element.get_attribute("href")
            except:
                # Essayer de trouver n'importe quel lien
                try:
                    link_element = article.find_element(By.CSS_SELECTOR, "a")
                    url = link_element.get_attribute("href")
                except:
                    continue
            
            # Extraire la date
            date = extract_date_from_article(article)
            
            if title and url and url.startswith("https://"):
                extracted_articles.append({
                    'date': date,
                    'title': title,
                    'url': url
                })
                print(f"Article extrait : {title[:60]}...")
                
        except Exception as e:
            continue
    
    return extracted_articles

def extract_date_from_article(article):
    """Tente d'extraire la date d'un article"""
    try:
        # Chercher différents sélecteurs de date
        date_selectors = [
            "time",
            "[datetime]",
            ".time",
            ".date",
            ".published-date",
            "[class*='date']",
            "[class*='time']"
        ]
        
        for selector in date_selectors:
            try:
                date_element = article.find_element(By.CSS_SELECTOR, selector)
                date_text = date_element.text.strip()
                datetime_attr = date_element.get_attribute("datetime")
                
                if datetime_attr:
                    # Parser la date ISO
                    try:
                        dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        return dt.strftime("%b %d, %Y")
                    except:
                        pass
                
                if date_text:
                    # Essayer de parser le texte de date
                    parsed_date = parse_date_text(date_text)
                    if parsed_date != "Unknown Date":
                        return parsed_date
                    
            except NoSuchElementException:
                continue
                
    except Exception:
        pass
    
    return "Unknown Date"

def parse_date_text(date_text):
    """Parse le texte de date en format standard"""
    # Patterns de date courants sur Medium
    patterns = [
        r'(\w{3})\s+(\d{1,2}),?\s+(\d{4})',  # "Feb 25, 2024"
        r'(\d{1,2})\s+(\w{3})\s+(\d{4})',   # "25 Feb 2024"
        r'(\w{3})\s+(\d{1,2})\s+(\d{4})',   # "Feb 25 2024"
        r'(\d{1,2})/(\d{1,2})/(\d{4})',     # "25/02/2024"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_text)
        if match:
            if len(match.groups()) == 3:
                month, day, year = match.groups()
                # Normaliser le format
                if month.isdigit():
                    # Si le mois est un nombre, le convertir en nom
                    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    try:
                        month = month_names[int(month) - 1]
                    except:
                        pass
                return f"{month} {day}, {year}"
    
    return "Unknown Date"

def load_existing_articles(csv_file):
    """Charge les articles existants du fichier CSV"""
    existing_articles = set()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                existing_articles.add(row['url'])
    except FileNotFoundError:
        print(f"Fichier {csv_file} non trouvé, création d'un nouveau fichier")
    
    return existing_articles

def save_articles_to_csv(articles, csv_file):
    """Sauvegarde les articles dans le fichier CSV"""
    # Charger les articles existants
    existing_urls = load_existing_articles(csv_file)
    
    # Filtrer les nouveaux articles
    new_articles = [article for article in articles if article['url'] not in existing_urls]
    
    if not new_articles:
        print("Aucun nouvel article à ajouter")
        return
    
    print(f"Ajout de {len(new_articles)} nouveaux articles au fichier CSV...")
    
    # Lire tous les articles existants
    all_articles = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            all_articles = list(reader)
    except FileNotFoundError:
        pass
    
    # Ajouter les nouveaux articles
    all_articles.extend(new_articles)
    
    # Sauvegarder dans le fichier CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['date', 'title', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(all_articles)
    
    print(f"Fichier {csv_file} mis à jour avec succès !")
    print(f"Total d'articles : {len(all_articles)}")

def main():
    """Fonction principale"""
    # URL de votre profil Medium
    medium_url = "https://louicop.medium.com"
    
    print("Démarrage du scraper Medium...")
    print(f"URL cible : {medium_url}")
    print(f"Architecture détectée : {platform.machine()}")
    
    driver = setup_driver()
    
    try:
        # Aller sur la page Medium
        print("Navigation vers Medium...")
        driver.get(medium_url)
        
        # Attendre que la page se charge
        time.sleep(5)
        
        # Faire défiler pour charger tous les articles
        scroll_to_bottom(driver)
        
        # Extraire tous les articles
        articles = extract_articles(driver)
        
        if articles:
            print(f"\nExtraction terminée ! {len(articles)} articles trouvés")
            
            # Sauvegarder dans le fichier CSV
            save_articles_to_csv(articles, "Blog.csv")
            
            # Afficher un résumé
            print("\nRésumé des articles extraits :")
            for i, article in enumerate(articles[:5], 1):  # Afficher les 5 premiers
                print(f"{i}. {article['title'][:60]}...")
            if len(articles) > 5:
                print(f"... et {len(articles) - 5} autres articles")
        else:
            print("Aucun article trouvé")
            
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        
    finally:
        driver.quit()
        print("Scraping terminé")

if __name__ == "__main__":
    main()
