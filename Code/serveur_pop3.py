import threading
from serveur_messagerie import ServeurMessagerie

"""
Auteurs       : Bohy, Abbadi, Cherraf 
Promotion     : M1 STRI     Date          : Janvier 2026       Version       : 3.0

DESCRIPTION :
Implémentation du serveur POP3 (Post Office Protocol).
Gère la consultation et la récupération des messages.
Chaque client reçoit son propre thread pour la communication.
"""

class ServeurPOP3(ServeurMessagerie):
    """Serveur POP3 - Consultation des messages"""
    
    def nom_protocole(self):
        return "POP3"
    
    def gerer_client(self, socket_client, adresse_client):
        """
        Gère la communication avec un client POP3
        
        Args:
            socket_client: Socket connectée au client
            adresse_client: Tuple (IP, port) du client
        """
        nom_thread = threading.current_thread().name
        print(f"[POP3] {nom_thread} : Connexion de {adresse_client}")
        
        with socket_client:
            # Envoie le message de bienvenue
            socket_client.sendall(b"+OK Service Ready\r\n")
            
            connexion_active = True
            
            while connexion_active:
                try:
                    # Reçoit les données du client
                    donnees_brutes = socket_client.recv(1024)
                    if not donnees_brutes:
                        break
                    
                    commande = donnees_brutes.decode('utf-8').strip()
                    print(f"[POP3] [{adresse_client}] Reçu: {commande}")
                    
                    # Traite la commande
                    connexion_active = self._traiter_commandes(commande, socket_client)
                
                except Exception as e:
                    print(f"[POP3] Erreur: {e}")
                    break
    
    def _traiter_commandes(self, commande, socket_client):
        """
        Traite une commande POP3
        
        Returns:
            bool: True si connexion active, False si QUIT
        """
        parties = commande.upper().split()
        if not parties:
            socket_client.sendall("-ERR Commande vide\r\n".encode('utf-8'))
            return True
        
        cmd = parties[0]
        
        match cmd:
            case "QUIT":
                socket_client.sendall("+OK Fermeture connexion\r\n".encode('utf-8'))
                return False
            
            case "STAT":
                self._traiter_stat(commande, socket_client)
            
            case "LIST":
                self._traiter_list(commande, socket_client)
            
            case "RETR":
                self._traiter_retr(commande, socket_client)
            
            case _:
                socket_client.sendall("-ERR Commande non implémentée\r\n".encode('utf-8'))
        
        return True
    
    def _traiter_stat(self, commande, socket_client):
        """
        Traite la commande STAT
        Format: STAT email@domain.com
        """
        parties = commande.split()
        if len(parties) < 2:
            socket_client.sendall("-ERR Erreur syntaxe\r\n".encode('utf-8'))
            return
        
        adresse_mail = parties[1]
        boite_mail = self.stockage.charger_boite_mail(adresse_mail)
        
        if boite_mail is None:
            socket_client.sendall("-ERR Boîte mail inexistante\r\n".encode('utf-8'))
        else:
            nb_messages = self.stockage.obtenir_nombre_messages(boite_mail)
            taille_totale = self.stockage.obtenir_taille_totale(boite_mail)
            socket_client.sendall(f"+OK {nb_messages} {taille_totale}\r\n".encode('utf-8'))
    
    def _traiter_list(self, commande, socket_client):
        """
        Traite la commande LIST
        Format: LIST email@domain.com
        """
        parties = commande.split()
        if len(parties) < 2:
            socket_client.sendall("-ERR Erreur syntaxe\r\n".encode('utf-8'))
            return
        
        adresse_mail = parties[1]
        boite_mail = self.stockage.charger_boite_mail(adresse_mail)
        
        if boite_mail is None:
            socket_client.sendall("-ERR Boîte mail inexistante\r\n".encode('utf-8'))
        else:
            liste_messages = self.stockage.obtenir_liste_messages(boite_mail)
            # Format: [[ID, expéditeur, taille], ...]
            socket_client.sendall(f"+OK {liste_messages}\r\n".encode('utf-8'))
    
    def _traiter_retr(self, commande, socket_client):
        """
        Traite la commande RETR
        Format: RETR indice email@domain.com
        """
        parties = commande.split()
        if len(parties) < 3 or not parties[1].isdigit():
            socket_client.sendall("-ERR Erreur syntaxe. Format: RETR indice email@domain.com\r\n".encode('utf-8'))
            return
        
        id_message = int(parties[1])
        adresse_mail = parties[2]
        boite_mail = self.stockage.charger_boite_mail(adresse_mail)
        
        if boite_mail is None:
            socket_client.sendall("-ERR Boîte mail inexistante\r\n".encode('utf-8'))
        elif not self.stockage.valider_id_message(id_message, boite_mail):
            socket_client.sendall("-ERR ID message inexistant\r\n".encode('utf-8'))
        else:
            message = self.stockage.obtenir_message(boite_mail, id_message)
            socket_client.sendall(f"+OK {message}\r\n".encode('utf-8'))
