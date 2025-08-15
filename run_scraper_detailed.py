#!/usr/bin/env python3
"""
Script détaillé pour scraper Medium en visitant chaque article individuellement
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
import re
from datetime import datetime

def setup_driver():
    """Configure le driver Chrome"""
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
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erreur avec ChromeDriver : {e}")
        raise e

def scroll_to_bottom(driver, max_scrolls=100):
    """Fait défiler la page jusqu'en bas pour charger tous les articles"""
    print("Défilement de la page pour charger tous les articles...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    no_change_count = 0
    
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_change_count += 1
            if no_change_count >= 3:
                print("Fin de la page atteinte")
                break
        else:
            no_change_count = 0
            
        last_height = new_height
        scroll_count += 1
        print(f"Défilement {scroll_count}/{max_scrolls}")
    
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

def extract_article_links(driver):
    """Extrait les liens vers les articles depuis la page principale"""
    print("Extraction des liens d'articles...")
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article, [data-testid='article']"))
        )
    except TimeoutException:
        print("Aucun article trouvé")
        return []
    
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
        return []
    
    article_links = []
    
    for i, article in enumerate(articles):
        try:
            # Extraire le titre
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
                try:
                    link_element = article.find_element(By.CSS_SELECTOR, "a")
                    url = link_element.get_attribute("href")
                except:
                    continue
            
            if title and url and url.startswith("https://"):
                article_links.append({
                    'title': title,
                    'url': url
                })
                print(f"Lien extrait {i+1}: {title[:50]}...")
                
        except Exception as e:
            continue
    
    return article_links

def extract_date_from_article_page(driver, url):
    """Extrait la date depuis la page individuelle de l'article"""
    try:
        print(f"  Visite de l'article pour extraire la date...")
        driver.get(url)
        time.sleep(3)
        
        # Attendre que la page se charge
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        
        # Stratégie 1: Chercher spécifiquement storyPublishDate
        try:
            story_date_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='storyPublishDate']")
            date_text = story_date_element.text.strip()
            if date_text:
                print(f"    Date trouvée via storyPublishDate: {date_text}")
                return date_text
        except NoSuchElementException:
            print(f"    storyPublishDate non trouvé, essai d'autres méthodes...")
        
        # Stratégie 2: Chercher dans les meta tags
        try:
            meta_elements = driver.find_elements(By.CSS_SELECTOR, "meta")
            for meta in meta_elements:
                property_attr = meta.get_attribute("property")
                content_attr = meta.get_attribute("content")
                
                if property_attr and "published" in property_attr.lower() and content_attr:
                    try:
                        dt = datetime.fromisoformat(content_attr.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%b %d, %Y")
                        print(f"    Date trouvée via meta tag: {formatted_date}")
                        return formatted_date
                    except:
                        pass
        except:
            pass
        
        # Stratégie 3: Essayer d'autres sélecteurs de date
        date_selectors = [
            "time[datetime]",
            "time",
            "[class*='date']",
            "[class*='time']",
            "[class*='published']",
            "[class*='timestamp']",
            "span[class*='date']",
            "div[class*='date']"
        ]
        
        for selector in date_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    # Vérifier l'attribut datetime
                    datetime_attr = element.get_attribute("datetime")
                    if datetime_attr:
                        try:
                            dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                            formatted_date = dt.strftime("%b %d, %Y")
                            print(f"    Date trouvée via {selector}: {formatted_date}")
                            return formatted_date
                        except:
                            pass
                    
                    # Vérifier le texte
                    date_text = element.text.strip()
                    if date_text:
                        parsed_date = parse_date_text_improved(date_text)
                        if parsed_date != "Unknown Date":
                            print(f"    Date trouvée via {selector}: {parsed_date}")
                            return parsed_date
                            
            except:
                continue
                
    except Exception as e:
        print(f"    Erreur lors de l'extraction de la date: {e}")
    
    return "Unknown Date"

def parse_date_text_improved(date_text):
    """Parse amélioré du texte de date"""
    date_text = re.sub(r'\s+', ' ', date_text.strip())
    
    patterns = [
        r'(\w{3})\s+(\d{1,2}),?\s+(\d{4})',  # "Feb 25, 2024"
        r'(\d{1,2})\s+(\w{3})\s+(\d{4})',   # "25 Feb 2024"
        r'(\w{3})\s+(\d{1,2})\s+(\d{4})',   # "Feb 25 2024"
        r'(\d{1,2})/(\d{1,2})/(\d{4})',     # "25/02/2024"
        r'(\d{1,2})-(\d{1,2})-(\d{4})',     # "25-02-2024"
        r'(\w{3})\s+(\d{1,2})',              # "Feb 25"
        r'(\d{1,2})\s+(\w{3})',              # "25 Feb"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_text)
        if match:
            if len(match.groups()) == 3:
                month, day, year = match.groups()
                if month.isdigit():
                    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    try:
                        month = month_names[int(month) - 1]
                    except:
                        pass
                return f"{month} {day}, {year}"
            elif len(match.groups()) == 2:
                month, day = match.groups()
                current_year = datetime.now().year
                if month.isdigit():
                    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    try:
                        month = month_names[int(month) - 1]
                    except:
                        pass
                return f"{month} {day}, {current_year}"
    
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
    existing_urls = load_existing_articles(csv_file)
    new_articles = [article for article in articles if article['url'] not in existing_urls]
    
    if not new_articles:
        print("Aucun nouvel article à ajouter")
        return
    
    print(f"Ajout de {len(new_articles)} nouveaux articles au fichier CSV...")
    
    all_articles = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            all_articles = list(reader)
    except FileNotFoundError:
        pass
    
    all_articles.extend(new_articles)
    
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['date', 'title', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(all_articles)
    
    print(f"Fichier {csv_file} mis à jour avec succès !")
    print(f"Total d'articles : {len(all_articles)}")

def main():
    """Fonction principale"""
    medium_url = "https://louicop.medium.com"
    
    print("Démarrage du scraper Medium détaillé...")
    print(f"URL cible : {medium_url}")
    print(f"Architecture détectée : {platform.machine()}")
    
    driver = setup_driver()
    
    try:
        # Aller sur la page Medium
        print("Navigation vers Medium...")
        driver.get(medium_url)
        time.sleep(5)
        
        # Faire défiler pour charger tous les articles
        scroll_to_bottom(driver)
        
        # Extraire les liens vers les articles
        article_links = extract_article_links(driver)
        
        if not article_links:
            print("Aucun lien d'article trouvé")
            return
        
        print(f"\nExtraction des liens terminée ! {len(article_links)} articles trouvés")
        
        # Maintenant, visiter chaque article pour extraire la date
        articles_with_dates = []
        
        for i, article_link in enumerate(article_links):
            print(f"\nTraitement de l'article {i+1}/{len(article_links)}: {article_link['title'][:50]}...")
            
            # Extraire la date depuis la page de l'article
            date = extract_date_from_article_page(driver, article_link['url'])
            
            articles_with_dates.append({
                'date': date,
                'title': article_link['title'],
                'url': article_link['url']
            })
            
            print(f"  Date extraite : {date}")
            
            # Petite pause pour ne pas surcharger Medium
            time.sleep(1)
        
        # Sauvegarder dans le fichier CSV
        save_articles_to_csv(articles_with_dates, "Blog.csv")
        
        # Afficher un résumé
        print("\nRésumé des articles extraits :")
        for i, article in enumerate(articles_with_dates[:5], 1):
            print(f"{i}. {article['title'][:50]}... | Date: {article['date']}")
        if len(articles_with_dates) > 5:
            print(f"... et {len(articles_with_dates) - 5} autres articles")
            
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        
    finally:
        driver.quit()
        print("Scraping terminé")

if __name__ == "__main__":
    main()
