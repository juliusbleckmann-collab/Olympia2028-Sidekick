"""Oeffnet die App in einem unsichtbaren Browser, damit Streamlit Community Cloud
sie nicht schlafen legt. Ist sie schon eingeschlafen, klickt das Skript den
Knopf zum Aufwecken. Es stellt keine Frage an den Sidekick, kostet also kein
Mistral-Guthaben.

Aufruf: python wach_halten.py https://dein-name.streamlit.app
"""
import re
import sys

from playwright.sync_api import TimeoutError as Zeitueberschreitung
from playwright.sync_api import sync_playwright

ERKENNUNG = "Fair-Play-Sidekick"     # Text, an dem die geladene App erkannt wird
AUFWECKEN = re.compile(r"get this app back up", re.IGNORECASE)
WARTEZEIT = 240                      # Sekunden, die die App zum Starten bekommt


def app_geladen(seite):
    """Die App laeuft auf Streamlit Cloud in einem eingebetteten Rahmen, daher alle Rahmen pruefen."""
    for rahmen in seite.frames:
        try:
            if rahmen.get_by_text(ERKENNUNG).count() > 0:
                return True
        except Exception:
            pass
    return False


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith("http"):
        sys.exit("Bitte die Adresse der App angeben, z. B. https://dein-name.streamlit.app")
    adresse = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        seite = browser.new_page()
        seite.goto(adresse, wait_until="domcontentloaded", timeout=90_000)

        geweckt = False
        for _ in range(WARTEZEIT // 5):
            if app_geladen(seite):
                print("App läuft." + (" (Sie wurde gerade aufgeweckt.)" if geweckt else ""))
                seite.wait_for_timeout(15_000)   # kurz offen bleiben, damit der Besuch zaehlt
                browser.close()
                return
            knopf = seite.get_by_role("button", name=AUFWECKEN)
            if not geweckt and knopf.count() > 0:
                print("App schläft, wecke sie auf …")
                try:
                    knopf.first.click(timeout=10_000)
                    geweckt = True
                except Zeitueberschreitung:
                    pass
            seite.wait_for_timeout(5_000)

        seite.screenshot(path="wach_halten_fehler.png", full_page=True)
        browser.close()
        sys.exit(f"Die App ist nach {WARTEZEIT} Sekunden nicht erreichbar. Bildschirmfoto: wach_halten_fehler.png")


if __name__ == "__main__":
    main()
