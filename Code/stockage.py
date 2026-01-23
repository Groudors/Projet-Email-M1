import os
import threading

"""
Auteurs       : Bohy, Abbadi, Cherraf 
Promotion     : M1 STRI     Date          : Janvier 2026       Version       : 3.0

DESCRIPTION :
Couche de stockage centralisée pour SMTP et POP3.
Gère la sauvegarde et le chargement des messages indépendamment du protocole.
Thread-safe grâce à un verrou (Lock) pour éviter les accès simultanés à la boîte mail.
"""

class StockageMessage:
    """Gère le stockage et la récupération des messages"""
    
    def __init__(self, dossier_mail='Boîte_mail'):
        self.dossier_mail = dossier_mail
        self.verrou = threading.Lock()  # Verrou pour la thread-safety
        self._initialiser_dossier()
    
    def _initialiser_dossier(self):
        """Crée le dossier de stockage s'il n'existe pas"""
        if not os.path.exists(self.dossier_mail):
            os.makedirs(self.dossier_mail)
    
    def _chemin_boite_mail(self, adresse_mail):
        """Retourne le chemin du fichier pour une adresse mail"""
        return os.path.join(self.dossier_mail, f"{adresse_mail}.txt")
    
    def sauvegarder_message(self, expediteur, destinataire, contenu_message):
        """
        Sauvegarde un message dans le fichier du destinataire
        
        Args:
            expediteur (str): Adresse de l'expéditeur
            destinataire (str): Adresse du destinataire
            contenu_message (list): Liste des lignes du message
        """
        if destinataire is None or expediteur is None:
            return False
        
        with self.verrou:  # Protection contre les accès simultanés
            chemin = self._chemin_boite_mail(destinataire)
            try:
                with open(chemin, 'a', encoding='utf-8') as f:
                    f.write(f"De: {expediteur}\n")
                    f.write(f"Pour: {destinataire}\n")
                    f.write("Message:\n")
                    f.write('\n'.join(contenu_message))
                    f.write("\n" + "="*50 + "\n\n")
                print(f"[Stockage] Message enregistré pour {destinataire}")
                return True
            except Exception as e:
                print(f"[Stockage] Erreur lors de la sauvegarde: {e}")
                return False
    
    def charger_boite_mail(self, adresse_mail):
        """
        Charge la boîte mail d'une adresse
        
        Args:
            adresse_mail (str): Adresse à charger
            
        Returns:
            dict: Dictionnaire des messages {id: {expediteur, contenu, taille}} ou None si inexistant
        """
        chemin = self._chemin_boite_mail(adresse_mail)
        
        if not os.path.exists(chemin):
            return None
        
        with self.verrou:  # Protection contre les accès simultanés
            boite_mail = {}
            try:
                with open(chemin, 'r', encoding='utf-8') as f:
                    contenu_complet = f.read()
                
                # Sépare les messages par le délimiteur
                messages = contenu_complet.split("="*50)
                
                id_mail = 1
                # Traite tous les messages sauf le dernier (vide après split)
                for message in messages[:-1]:
                    taille = len(message.encode('utf-8'))
                    message_nettoye = message.strip()
                    
                    # Extrait l'expéditeur
                    expediteur = "Inconnu"
                    for ligne in message_nettoye.split('\n'):
                        if ligne.startswith('De:'):
                            expediteur = ligne.replace('De:', '').strip()
                            break
                    
                    boite_mail[id_mail] = {
                        "expediteur": expediteur,
                        "contenu": message_nettoye,
                        "taille": taille
                    }
                    id_mail += 1
                
                return boite_mail
            except Exception as e:
                print(f"[Stockage] Erreur lors du chargement: {e}")
                return None
    
    def obtenir_nombre_messages(self, boite_mail):
        """Retourne le nombre de messages"""
        return len(boite_mail) if boite_mail else 0
    
    def obtenir_taille_totale(self, boite_mail):
        """Retourne la taille totale de la boîte mail"""
        if not boite_mail:
            return 0
        return sum(msg['taille'] for msg in boite_mail.values())
    
    def obtenir_liste_messages(self, boite_mail):
        """Retourne la liste des messages avec ID, expéditeur et taille"""
        if not boite_mail:
            return []
        return [[id_msg, boite_mail[id_msg]['expediteur'], boite_mail[id_msg]['taille']] 
                for id_msg in boite_mail]
    
    def obtenir_message(self, boite_mail, id_msg):
        """Retourne le contenu d'un message spécifique"""
        if id_msg in boite_mail:
            return boite_mail[id_msg]['contenu']
        return None
    
    def valider_id_message(self, id_msg, boite_mail):
        """Vérifie si un ID de message existe"""
        return id_msg in boite_mail if boite_mail else False
