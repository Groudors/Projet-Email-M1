import threading
from serveur_messagerie import ServeurMessagerie

"""
Auteurs       : Bohy, Abbadi, Cherraf 
Promotion     : M1 STRI     Date          : Janvier 2026       Version       : 3.0

DESCRIPTION :
Implémentation du serveur SMTP (Simple Mail Transfer Protocol).
Gère la réception et la sauvegarde des messages.
Chaque client reçoit son propre thread pour la communication.
"""

class ServeurSMTP(ServeurMessagerie):
    """Serveur SMTP - Réception de messages"""
    
    def nom_protocole(self):
        return "SMTP"
    
    def gerer_client(self, socket_client, adresse_client):
        """
        Gère la communication avec un client SMTP
        
        Args:
            socket_client: Socket connectée au client
            adresse_client: Tuple (IP, port) du client
        """
        nom_thread = threading.current_thread().name
        print(f"[SMTP] {nom_thread} : Connexion de {adresse_client}")
        
        with socket_client:
            # Envoie le message de bienvenue
            socket_client.sendall(b"220 Service Ready\r\n")
            
            # Variables de session pour ce client
            expediteur = None
            destinataire = None
            mode_data = False
            contenu_message = []
            connexion_active = True
            
            while connexion_active:
                try:
                    # Reçoit les données du client
                    donnees_brutes = socket_client.recv(1024)
                    if not donnees_brutes:
                        break
                    
                    commande = donnees_brutes.decode('utf-8').strip()
                    
                    # Affiche la commande (sauf le point '.' de fin de DATA)
                    if commande != ".":
                        print(f"[SMTP] [{adresse_client}] Reçu: {commande}")
                    
                    # Deux cas : soit on reçoit une commande, soit on est en mode DATA
                    if not mode_data:
                        # Traite les commandes SMTP
                        expediteur, destinataire, mode_data, contenu_message, connexion_active = \
                            self._traiter_commandes(commande, socket_client, expediteur, 
                                                   destinataire, mode_data, contenu_message)
                    else:
                        # En mode DATA, on collecte les lignes du message
                        if commande == ".":
                            # Fin du message
                            socket_client.sendall("250 OK\r\n".encode('utf-8'))
                            mode_data = False
                            
                            # Sauvegarde le message
                            self.stockage.sauvegarder_message(expediteur, destinataire, contenu_message)
                            
                            # Réinitialise pour le prochain message
                            contenu_message = []
                            expediteur = None
                            destinataire = None
                        else:
                            # Ajoute la ligne au contenu
                            contenu_message.append(commande)
                
                except Exception as e:
                    print(f"[SMTP] Erreur: {e}")
                    break
    
    def _traiter_commandes(self, commande, socket_client, expediteur, destinataire, 
                          mode_data, contenu_message):
        """
        Traite une commande SMTP
        
        Returns:
            Tuple: (expediteur, destinataire, mode_data, contenu_message, connexion_active)
        """
        parties = commande.upper().split()
        if not parties:
            socket_client.sendall("502 Commande non implémentée\r\n".encode('utf-8'))
            return expediteur, destinataire, mode_data, contenu_message, True
        
        cmd = parties[0]
        
        match cmd:
            case "EHLO":
                socket_client.sendall("502 Commande non implémentée\r\n".encode('utf-8'))
            
            case "HELO":
                socket_client.sendall("250 Ok\r\n".encode('utf-8'))
            
            case "MAIL":
                expediteur = self._traiter_mail_from(commande, socket_client)
            
            case "RCPT":
                destinataire = self._traiter_rcpt_to(commande, socket_client)
            
            case "DATA":
                socket_client.sendall("354 Envoyez votre mail.\r\n".encode('utf-8'))
                mode_data = True
            
            case "QUIT":
                socket_client.sendall("221 Fermeture connexion\r\n".encode('utf-8'))
                return expediteur, destinataire, mode_data, contenu_message, False
            
            case _:
                socket_client.sendall("502 Commande non implémentée\r\n".encode('utf-8'))
        
        return expediteur, destinataire, mode_data, contenu_message, True
    
    def _traiter_mail_from(self, commande, socket_client):
        """Extrait l'adresse de l'expéditeur"""
        if "FROM:" in commande.upper():
            expediteur = commande.split("FROM:", 1)[1].strip().strip('<>')
            socket_client.sendall("250 Sender OK\r\n".encode('utf-8'))
            return expediteur
        socket_client.sendall("501 Erreur syntaxe\r\n".encode('utf-8'))
        return None
    
    def _traiter_rcpt_to(self, commande, socket_client):
        """Extrait l'adresse du destinataire"""
        if "TO:" in commande.upper():
            destinataire = commande.split("TO:", 1)[1].strip().strip('<>')
            socket_client.sendall("250 Recipient OK\r\n".encode('utf-8'))
            return destinataire
        socket_client.sendall("501 Erreur syntaxe\r\n".encode('utf-8'))
        return None
