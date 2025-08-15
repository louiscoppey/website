#!/usr/bin/env python3
"""
Script de débogage pour inspecter la structure HTML de Medium et trouver les dates
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Configure le driver Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def debug_article_page(url):
    """Débogue une page d'article pour trouver la structure des dates"""
    driver = setup_driver()
    
    try:
        print(f"Visite de l'article : {url}")
        driver.get(url)
        time.sleep(5)
        
        print("Page chargée, inspection en cours...")
        
        # Attendre que la page se charge
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            print("Body trouvé")
        except:
            print("Body non trouvé, mais on continue...")
        
        print("\n=== INSPECTION DE LA PAGE ===")
        
        # Chercher tous les éléments qui pourraient contenir des dates
        date_related_selectors = [
            "[data-testid*='date']",
            "[data-testid*='time']",
            "[data-testid*='publish']",
            "[class*='date']",
            "[class*='time']",
            "[class*='publish']",
            "time",
            "[datetime]"
        ]
        
        print("\n--- Éléments liés aux dates ---")
        for selector in date_related_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\nSélecteur '{selector}' : {len(elements)} éléments trouvés")
                    for i, elem in enumerate(elements[:3]):  # Afficher les 3 premiers
                        try:
                            text = elem.text.strip()
                            datetime_attr = elem.get_attribute("datetime")
                            class_attr = elem.get_attribute("class")
                            data_testid = elem.get_attribute("data-testid")
                            
                            print(f"  Élément {i+1}:")
                            print(f"    Texte: '{text}'")
                            print(f"    Datetime: '{datetime_attr}'")
                            print(f"    Class: '{class_attr}'")
                            print(f"    Data-testid: '{data_testid}'")
                        except Exception as e:
                            print(f"    Erreur lors de l'inspection: {e}")
                else:
                    print(f"Sélecteur '{selector}' : aucun élément trouvé")
            except Exception as e:
                print(f"Erreur avec le sélecteur '{selector}': {e}")
        
        # Chercher dans le HTML source
        print("\n--- INSPECTION DU HTML SOURCE ---")
        page_source = driver.page_source
        print(f"Taille du HTML source : {len(page_source)} caractères")
        
        # Chercher des patterns de date
        import re
        date_patterns = [
            r'storyPublishDate["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'publishDate["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'date["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'time["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'published["\']?\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                print(f"\nPattern '{pattern}' trouvé:")
                for match in matches[:5]:  # Afficher les 5 premiers
                    print(f"  - {match}")
            else:
                print(f"Pattern '{pattern}' : aucun match trouvé")
        
        # Chercher des éléments avec des attributs data-testid
        data_testid_pattern = r'data-testid=["\']([^"\']+)["\']'
        data_testids = re.findall(data_testid_pattern, page_source)
        if data_testids:
            print(f"\n--- Tous les data-testid trouvés ---")
            unique_testids = list(set(data_testids))
            for testid in sorted(unique_testids):
                print(f"  - {testid}")
        else:
            print("Aucun data-testid trouvé")
        
        # Chercher des éléments avec des classes contenant "date" ou "time"
        class_pattern = r'class=["\']([^"\']*?(?:date|time|publish)[^"\']*?)["\']'
        classes = re.findall(class_pattern, page_source)
        if classes:
            print(f"\n--- Classes contenant date/time/publish ---")
            unique_classes = list(set(classes))
            for class_name in sorted(unique_classes):
                print(f"  - {class_name}")
        else:
            print("Aucune classe contenant date/time/publish trouvée")
        
        # Chercher des patterns de date dans le texte
        print("\n--- Recherche de patterns de date dans le texte ---")
        text_patterns = [
            r'(\w{3}\s+\d{1,2},?\s+\d{4})',  # "Feb 25, 2024"
            r'(\d{1,2}\s+\w{3}\s+\d{4})',   # "25 Feb 2024"
            r'(\d{1,2}/\d{1,2}/\d{4})',     # "25/02/2024"
        ]
        
        for pattern in text_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                print(f"\nPattern de date '{pattern}' trouvé:")
                unique_matches = list(set(matches))
                for match in unique_matches[:10]:  # Afficher les 10 premiers
                    print(f"  - {match}")
            else:
                print(f"Pattern de date '{pattern}' : aucun match trouvé")
                
    except Exception as e:
        print(f"Erreur lors du débogage : {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

def main():
    """Fonction principale"""
    # Test avec un article spécifique
    test_url = "https://louicop.medium.com/agents-powered-b2b-marketplaces-opportunities-for-ai-agents-in-a-marketplace-context-6a6438a6789e"
    
    print("Démarrage du débogage des dates Medium...")
    debug_article_page(test_url)

if __name__ == "__main__":
    main()
