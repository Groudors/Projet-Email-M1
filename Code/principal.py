import threading
from stockage import StockageMessage
from serveur_smtp import ServeurSMTP
from serveur_pop3 import ServeurPOP3

"""
Auteurs: Bohy, Abbadi, Cherraf 
Promotion: M1 STRI     Date  : Janvier 2026       Version : 3.0

DESCRIPTION :
Point d'entrée unique pour lancer les serveurs SMTP et POP3.
Les deux serveurs s'exécutent simultanément dans des threads séparés.

ARCHITECTURE :
Thread Principal
    ├─ Thread Serveur SMTP (port 65434)
    │   ├─ Accepte les connexions SMTP
    │   ├─ Thread Client SMTP 1 (gère la communication)
    │   ├─ Thread Client SMTP 2
    │   └─ ...
    │
    └─ Thread Serveur POP3 (port 65433)
        ├─ Accepte les connexions POP3
        ├─ Thread Client POP3 1 (gère la communication)
        ├─ Thread Client POP3 2
        └─ ...

La classe StockageMessage est partagée entre les deux serveurs,
avec un verrou (Lock) pour éviter les accès simultanés au fichiers.
"""

def main():
    # Initialise le stockage partagé
    stockage = StockageMessage('Boîte_mail')
    
    # Crée les instances des serveurs
    serveur_smtp = ServeurSMTP(port=65434, stockage=stockage)
    serveur_pop3 = ServeurPOP3(port=65433, stockage=stockage)
    
    # Lance chaque serveur dans son propre thread
    thread_smtp = threading.Thread(target=serveur_smtp.demarrer, name="ServeurSMTP")
    thread_pop3 = threading.Thread(target=serveur_pop3.demarrer, name="ServeurPOP3")
    
    # Les threads daemon se terminent quand le programme principal s'arrête
    thread_smtp.daemon = False
    thread_pop3.daemon = False
    
    print("=" * 60)
    print("=== Serveurs de Messagerie - Démarrage ===")
    print("=" * 60)
    print("SMTP : localhost:65434")
    print("POP3 : localhost:65433")
    print("(Appuyez sur Ctrl+C pour arrêter)\n")
    
    try:
        thread_smtp.start()
        thread_pop3.start()
        
        # Attend que les threads se terminent
        thread_smtp.join()
        thread_pop3.join()
    
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Arrêt demandé. Fermeture des serveurs...")
        print("(Attente de la fin des clients en cours...)")
        print("=" * 60)
        serveur_smtp.arreter()
        serveur_pop3.arreter()
        
        # Attend que les threads serveurs finissent
        print("\nFermeture en cours...\n")
        thread_smtp.join()
        thread_pop3.join()
        
        print("\n" + "=" * 60)
        print("** Serveur SMTP fermé **")
        print("** Serveur POP3 fermé **")
        print("=" * 60)
        print("\n À bientôt !\n")

if __name__ == "__main__":
    main()
