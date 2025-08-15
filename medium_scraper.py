#!/usr/bin/env python3
"""
Script pour scraper tous les articles Medium de l'utilisateur
et les ajouter au fichier Blog.csv existant
"""

import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from datetime import datetime

def setup_driver():
    """Configure le driver Chrome avec les options appropriées"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans interface graphique
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scroll_to_bottom(driver, max_scrolls=50):
    """Fait défiler la page jusqu'en bas pour charger tous les articles"""
    print("Défilement de la page pour charger tous les articles...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        # Faire défiler jusqu'en bas
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Attendre que la page se charge
        time.sleep(2)
        
        # Calculer la nouvelle hauteur
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Si la hauteur n'a pas changé, on a atteint le bas
        if new_height == last_height:
            print("Fin de la page atteinte")
            break
            
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )
    except TimeoutException:
        print("Aucun article trouvé")
        return []
    
    # Trouver tous les articles
    articles = driver.find_elements(By.CSS_SELECTOR, "article")
    print(f"Nombre d'articles trouvés : {len(articles)}")
    
    extracted_articles = []
    
    for article in articles:
        try:
            # Extraire le titre
            title_element = article.find_element(By.CSS_SELECTOR, "h2, h3, h4")
            title = title_element.text.strip()
            
            # Extraire l'URL
            link_element = article.find_element(By.CSS_SELECTOR, "a[href*='medium.com']")
            url = link_element.get_attribute("href")
            
            # Extraire la date (si disponible)
            date = extract_date_from_article(article)
            
            if title and url:
                extracted_articles.append({
                    'date': date,
                    'title': title,
                    'url': url
                })
                print(f"Article extrait : {title[:50]}...")
                
        except NoSuchElementException as e:
            continue
        except Exception as e:
            print(f"Erreur lors de l'extraction d'un article : {e}")
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
            ".published-date"
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
                    return parse_date_text(date_text)
                    
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
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_text)
        if match:
            if len(match.groups()) == 3:
                month, day, year = match.groups()
                # Normaliser le format
                return f"{month} {day}, {year}"
    
    return date_text

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

