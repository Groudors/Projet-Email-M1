import socket
import threading
from abc import ABC, abstractmethod

"""
Auteurs: Bohy, Abbadi, Cherraf 
Promotion: M1 STRI     Date  : Janvier 2026       Version : 3.0

DESCRIPTION :
Classe abstraite de base pour les serveurs de messagerie.
Gère la boucle d'écoute commune aux protocoles SMTP et POP3.

ARCHITECTURE DES THREADS :
    - Thread Principal : lance les 2 serveurs
        ├─ Thread Serveur SMTP : boucle d'écoute sur le port 65434
        │   ├─ Thread Client SMTP 1 : gère la communication avec le client 1
        │   ├─ Thread Client SMTP 2 : gère la communication avec le client 2
        │   └─ ...
        └─ Thread Serveur POP3 : boucle d'écoute sur le port 65433
            ├─ Thread Client POP3 1 : gère la communication avec le client 1
            ├─ Thread Client POP3 2 : gère la communication avec le client 2
            └─ ...

Chaque serveur écoute sur son propre port dans un thread dédié.
Chaque client qui se connecte est géré dans son propre thread, 
permettant plusieurs connexions simultanées sans blocage.
"""

class ServeurMessagerie(ABC):
    """Classe de base abstraite pour les serveurs SMTP et POP3"""
    
    def __init__(self, port, stockage):
        """
        Initialise le serveur
        
        Args:
            port (int): Port d'écoute
            stockage (StockageMessage): Instance du gestionnaire de stockage
        """
        self.port = port
        self.stockage = stockage
        self.en_execution = False
        self.socket_ecoute = None
        self.threads_clients = []  # Liste pour garder trace des threads clients
        self.deja_arrête = False  # Guard pour éviter l'appel double
    
    def demarrer(self):
        """Lance le serveur dans la boucle d'écoute"""
        self.en_execution = True
        self.socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_ecoute.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket_ecoute.bind(('', self.port))
            self.socket_ecoute.listen()
            self.socket_ecoute.settimeout(1.0)
            
            print(f"[{self.nom_protocole()}] Serveur démarré sur le port {self.port}")
            
            # Boucle d'écoute : accepte les connexions
            self._boucle_ecoute()
        
        except Exception as e:
            print(f"[{self.nom_protocole()}] Erreur: {e}")
        finally:
            self.arreter()
    
    def _boucle_ecoute(self):
        """Accepte les connexions et crée un thread par client"""
        while self.en_execution:
            try:
                # Attend une connexion client
                socket_client, adresse_client = self.socket_ecoute.accept()
                
                # Crée un thread pour gérer ce client
                thread_client = threading.Thread(
                    target=self.gerer_client,
                    args=(socket_client, adresse_client),
                    daemon=False  # Ne pas terminer immédiatement
                )
                thread_client.start()
                self.threads_clients.append(thread_client)  # Garde trace du thread
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.en_execution:
                    print(f"[{self.nom_protocole()}] Erreur lors de l'acceptation: {e}")
    
    def arreter(self):
        """Arrête le serveur et attend que les clients finissent"""
        if self.deja_arrête:
            return
        
        self.deja_arrête = True
        self.en_execution = False
        if self.socket_ecoute:
            try:
                self.socket_ecoute.close()
            except:
                pass
        
        # Attend que tous les threads clients se terminent
        for thread in self.threads_clients:
            thread.join() 
        
        print(f"[{self.nom_protocole()}] Serveur arrêté")
    
    @abstractmethod
    def nom_protocole(self):
        """Retourne le nom du protocole (à implémenter par les sous-classes)"""
        pass
    
    @abstractmethod
    def gerer_client(self, socket_client, adresse_client):
        """
        Gère la communication avec un client (à implémenter par les sous-classes)
        
        Args:
            socket_client: Socket connectée au client
            adresse_client: Adresse IP du client
        """
        pass
