import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import random

# Selenium & Webdriver Manager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="Scraper Menu Furtif", page_icon="🥷", layout="wide")

st.title("🥷 Auto-Scraper : Mode Furtif (Anti-Bot)")
st.markdown("""
Ce mode utilise des techniques avancées pour masquer le robot Selenium :
* Modification du User-Agent
* Désactivation des indicateurs d'automatisation
* Masquage de la variable `navigator.webdriver`
""")

# --- 1. Configuration Navigateur Furtif ---
def get_driver():
    chrome_options = Options()
    
    # --- LES REGLAGES CRITIQUES POUR EVITER LE BLOCAGE ---
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") # Masque le contrôle auto
    
    # On se fait passer pour un vrai PC Windows avec Chrome récent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Configuration Streamlit Cloud
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Configuration Locale (PC)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

    # --- L'ASTUCE ULTIME ---
    # On injecte du Javascript pour effacer les traces de Selenium
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
    })
    
    return driver

# --- 2. Extraction Intelligente (Stratégie 'Argent') ---
def extract_menu_data(soup):
    data = []
    seen_texts = set()
    
    # Regex pour trouver les prix (MAD, Dhs, etc)
    price_pattern = re.compile(r'(\d+[\.,]?\d*\s*(?:MAD|Dhs|DH|€|\$)|(?:MAD|Dhs|DH|€|\$)\s*\d+[\.,]?\d*)', re.IGNORECASE)
    
    # On cherche tous les textes
    all_elements = soup.find_all(['div', 'span', 'p'])
    
    for el in all_elements:
        text = el.get_text(" | ", strip=True)
        
        # Si le texte contient un prix ET n'est pas trop long (pour éviter de prendre tout le footer)
        if price_pattern.search(text) and 10 < len(text) < 300:
            if text not in seen_texts:
                
                # Extraction basique
                match_price = price_pattern.search(text)
                prix = match_price.group(0)
                
                # On essaie de séparer le titre
                parts = text.split('|')
                titre = parts[0].strip()
                if len(titre) < 3 and len(parts) > 1: titre = parts[1].strip()
                
                data.append({
                    'Produit (Deviné)': titre,
                    'Prix': prix,
                    'Texte Complet': text
                })
                seen_texts.add(text)
    
    return data

# --- 3. Interface ---
url = st.text_input("URL du Menu (Glovo, etc.)", placeholder="https://glovoapp.com/...")

if st.button("Lancer l'Extraction Furtive 🕵️‍♂️"):
    if url:
        status = st.empty()
        status.info("Démarrage du mode furtif...")
        
        driver = None
        try:
            driver = get_driver()
            
            status.info("Connexion au site...")
            driver.get(url)
            
            # Pause aléatoire pour faire 'humain'
            time.sleep(random.uniform(3, 5))
            
            status.info("Simulation de lecture (Scroll)...")
            # On scroll doucement
            for i in range(1, 5):
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/5});")
                time.sleep(random.uniform(1, 2))
            
            # Scroll final
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            status.info("Analyse du contenu chargé...")
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            results = extract_menu_data(soup)
            
            if results:
                st.success(f"Réussite ! {len(results)} éléments extraits.")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Télécharger CSV", csv, "menu_furtif.csv", "text/csv")
            else:
                st.warning("Le site résiste encore. Il charge peut-être les données via une API cachée.")
                # Debug léger pour voir si on a passé la barrière Next.js
                debug_title = soup.title.string if soup.title else "Sans titre"
                st.text(f"Titre de la page capturée : {debug_title}")

        except Exception as e:
            st.error(f"Erreur : {e}")
        finally:
            if driver: driver.quit()
            status.empty()
