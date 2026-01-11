import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import time
import re

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="Scraper Glovo Force", page_icon="⚡", layout="wide")

st.title("⚡ Auto-Scraper : Mode 'Chercher l'Argent'")
st.markdown("""
Ce mode ignore la structure du site. Il cherche simplement **le symbole monétaire (MAD, Dhs)** et capture le texte autour. Très efficace pour les sites difficiles.
""")

# --- 1. Configuration Navigateur ---
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080") # Important pour voir tout le menu
    
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# --- 2. Nouvelle Logique de Détection ---
def extract_by_currency(soup):
    data = []
    seen_texts = set() # Pour éviter les doublons
    
    # On cherche le texte visible qui contient un prix
    # Regex : Chiffre + Espace(optionnel) + (MAD ou Dhs ou DH)
    price_pattern = re.compile(r'(\d+[\.,]?\d*\s*(?:MAD|Dhs|DH|€|\$)|(?:MAD|Dhs|DH|€|\$)\s*\d+[\.,]?\d*)', re.IGNORECASE)
    
    # On trouve tous les élements terminaux (bout de texte) qui contiennent un prix
    price_elements = soup.find_all(string=price_pattern)
    
    for price_text in price_elements:
        # On remonte de 3 niveaux pour attraper le conteneur du plat (Titre + Desc + Prix)
        container = price_text.find_parent()
        
        # On essaie de remonter jusqu'à trouver un bloc cohérent (div)
        for _ in range(4):
            if container.name in ['div', 'article', 'li'] and len(container.get_text(strip=True)) > 10:
                break
            if container.parent:
                container = container.parent
        
        full_text = container.get_text(" | ", strip=True)
        
        # Nettoyage et Filtres
        if full_text not in seen_texts:
            # On ignore les textes trop longs (c'est probablement tout le site) ou trop courts
            if 10 < len(full_text) < 400:
                
                # Extraction basique
                match_price = price_pattern.search(full_text)
                prix = match_price.group(0) if match_price else "N/A"
                
                # Le titre est souvent la partie avant le prix ou au début
                parts = full_text.split('|')
                titre = parts[0].strip()
                
                # Si le titre est le prix, on prend le suivant
                if titre in prix and len(parts) > 1:
                    titre = parts[1].strip()

                data.append({
                    'Titre Estimé': titre,
                    'Prix': prix,
                    'Texte Complet': full_text
                })
                seen_texts.add(full_text)
    
    return data

# --- 3. Interface ---
url = st.text_input("URL Glovo / Jumia / etc :", placeholder="https://glovoapp.com/...")

if st.button("Lancer le Scan 🕵️"):
    if url:
        status = st.empty()
        status.info("Démarrage du navigateur...")
        
        driver = get_driver()
        try:
            driver.get(url)
            status.info("Chargement... (Veuillez patienter 5s)")
            time.sleep(5)
            
            # Gros scroll pour être sûr
            status.info("Scroll vers le bas pour charger les images...")
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            status.info("Extraction des données...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            results = extract_by_currency(soup)
            
            if results:
                st.success(f"Bingo ! {len(results)} plats trouvés via détection de devise.")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Télécharger CSV", csv, "menu_extract.csv", "text/csv")
            else:
                st.error("Toujours rien. Le site utilise peut-être des iframes ou bloque l'IP.")
                st.text("Debug - HTML partiel : " + str(driver.page_source)[:500])
                
        except Exception as e:
            st.error(f"Erreur technique : {e}")
        finally:
            driver.quit()
            status.empty()
