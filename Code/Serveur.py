import threading
import os
import socket

"""
Auteurs       : Bohy, Abbadi, Cherraf 
Promotion     : M1 STRI     Date          : Janvier 2026       Version       : 2.0 (SMTP Simple)

DESCRIPTION :
Ce programme implémente un serveur de messagerie électronique basique respectant
une partie du protocole SMTP (Simple Mail Transfer Protocol - RFC 5321).

FONCTIONNALITÉS (VERSION 2.0) :
   Architecture Serveur TCP Multithreadé :
     Socket d'écoute sur le port 65434
     Gestion de chaque client dans un thread dédié  pour permettre des connexions simultanées sans blocage.

   Gestion des commandes SMTP :
     EHLO      : Identification du client (retourne 502 - non implémenté).
     HELO      : Identification du client (implémenté - retourne 250 OK).
     MAIL FROM : Identification de l'expéditeur.
     RCPT TO   : Identification du destinataire.
     DATA      : Réception du corps du message (terminé par un point '.').
     QUIT      : Clôture propre de la connexion.

   Compatibilité :
     Compatible avec les clients SMTP standards incluant Thunderbird.

   Stockage :
     Les courriels reçus sont sauvegardés dans des fichiers textes locaux, le nom du fichier correspond à l'adresse du destinataire (RCPT).

"""

# Configuration des valeurs de base
HOTE = ''
PORT = 65434
DOSSIER_MAIL = 'Boîte_mail'

stop_server = False

# =============================================== Partie Initialisation Serveur ===============================================

def initialisation_serveur():   
    # On crée le dossier de stockage des mails s'il n'existe pas
    if not os.path.exists(DOSSIER_MAIL):
        os.makedirs(DOSSIER_MAIL)

    # Création de la socket d'écoute
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ecoute:
        # Liaison de la socket d'écoute 
        ecoute.bind(('', PORT))
        # Ouverture du service
        ecoute.listen()
        ecoute.settimeout(1.0)
    
        while not stop_server:
            # Attente et acceptation d'une nouvelle connexion
            try:
                service, addr = ecoute.accept()
            except socket.timeout:
                continue

            # Dès que l'on accepte une connexion, on crée un thread pour gérer ce client
            thread_serveur = threading.Thread(target=gestion_client, args=(service, addr))
            thread_serveur.start()



#  =============================================== Partie Gestion Client / Commandes ===============================================

def gestion_client(service, adresse):
    # Gère la communication avec un client SMTP

    print(f"{threading.current_thread().name} : Connexion de l'adresse : {adresse}")
    with service:
        # Envoie du message de confirmation de mise en place du service
        service.sendall(b"220 Service Ready\n")
        expediteur = None
        destinataire = None
        mode_data = False # Indique si on est en mode réception de données avec DATA
        contenu_message = []
        Condition_fin_connection=True
        dictionnaire_mails = {}
    
        while Condition_fin_connection:
            # On réceptionne des données du client
            data = service.recv(1024)
            if not data:
                break  # Connexion fermée par le client en cas d'erreur ou autre
            
            donnees = data.decode('utf-8').strip()
            if donnees != ".":  
                print(f"[{adresse}] Reçu: {donnees}")

            # Si le message précédant n'était pas "DATA", on envoie dans gestion_commandes pour trouver le type de commande
            if (mode_data is False):
                expediteur,destinataire,mode_data,contenu_message,Condition_fin_connection=gestion_commandes(donnees,service,expediteur,destinataire,mode_data,contenu_message)
           
            # Sinon, l'envoie de données est activé
            else:
                # En mode DATA, on collecte les lignes du message
                if donnees == ".":
                    service.sendall("250 OK\r\n".encode('utf-8'))
                    # Fin de la saisie du message
                    mode_data = False
                    # Sauvegarde le message dans un fichier
                    sauvegarder_message(expediteur, destinataire, contenu_message)
                    contenu_message = []  # Réinitialise le contenu du message pour le prochain
                else:
                    # Ajoute la ligne au contenu du message
                    contenu_message.append(donnees)





def gestion_commandes(donnees,service,expediteur,destinataire,mode_data,contenu_message):
    # Plus besoin de passer dictionnaire_mails, on le charge dans les cases qui en ont besoin
    commande = donnees.upper().split()[0] 
    match commande:
        # Gestion de EHLO (SMTP complexe non implémenté)
        case "EHLO":
            service.sendall("502 Command not implemented\r\n".encode('utf-8'))

        # Gestion de HELO (SMTP implémenté)
        case "HELO":
            # On répond 250 OK
            service.sendall("250 Ok\r\n".encode('utf-8'))
            
        # Cas MAIL FROM:<adresse>
        case "MAIL":
            expediteur = facto_mail_from(donnees,service)
        
        # Gestion reception du message
        case "RCPT":
            destinataire = facto_rcpt_to(donnees,service)
        
        # Gestion de la commande DATA 
        case "DATA":
            service.sendall("354 Envoyez votre mail. \r\n".encode('utf-8'))
            mode_data = True
        
        case "QUIT":
            service.sendall("221 fermeture connexion\r\n".encode('utf-8'))
            return expediteur,destinataire,mode_data,contenu_message,False  

        case "STAT":
            facto_stat(donnees,service)
        
        case "LIST":
            facto_list(donnees,service)
        
        case "RETR":
            facto_retr(donnees,service)

        case _:
            service.sendall("502 Command not implemented\r\n".encode('utf-8'))
    return expediteur,destinataire,mode_data,contenu_message,True    




# ================================================ Partie Code Auxiliaire ================================================

# ================================== Factorisation de gestion des commandes ==============================================

def facto_mail_from(donnees,service):
    # Extrait l'adresse e-mail de l'expéditeur de la commande MAIL FROM
    if "FROM:" in donnees.upper():
        expediteur = donnees.split("FROM:",1)[1].strip().strip('<>')
        service.sendall("250 Sender OK\r\n".encode('utf-8'))
        return expediteur
    service.sendall("501 Erreur syntaxe\r\n".encode('utf-8'))
    return None


def facto_rcpt_to(donnees,service):
    # Extrait l'adresse e-mail du destinataire de la commande RCPT TO
    if "TO:" in donnees.upper():
        destinataire = donnees.split("TO:",1)[1].strip().strip('<>')
        service.sendall("250 Recipient OK\r\n".encode('utf-8'))
        return destinataire
    service.sendall("501 Erreur syntaxe\r\n".encode('utf-8'))
    return None

# ================================== Partie Sauvegarde des messages ==============================================

def sauvegarder_message(expediteur, destinataire, contenu_message):
    #Sauvegarde le message dans un fichier correspondant au destinataire

    if destinataire is not None and expediteur is not None:
        fichier_mail = os.path.join(DOSSIER_MAIL, f"{destinataire}.txt")
        with open(fichier_mail, 'a', encoding='utf-8') as f:
            f.write(f"De: {expediteur}\n")
            f.write(f"Pour: {destinataire}\n")
            f.write("Message:\n")
            f.write('\n'.join(contenu_message))
            f.write("\n" + "="*50 + "\n\n")
        print(f"Message enregistré dans {fichier_mail}")

# ================================= Partie Commandes Factorisation POP3 ==============================================
def facto_stat(donnees, service):
    # Format reçu: "STAT email@domain.com"
            parties = donnees.split()
            if len(parties) >= 2:
                destinataire = parties[1]
                dictionnaire_mails = charger_boite_mail(destinataire)
                if dictionnaire_mails is not None:
                    nbr, taille = commande_stat(dictionnaire_mails)
                    service.sendall(f"{nbr} {taille}\r\n".encode('utf-8'))
                else:
                    service.sendall("501 Boîte mail inexistante\r\n".encode('utf-8'))
            else:
                service.sendall("501 Erreur syntaxe\r\n".encode('utf-8'))

def facto_list(donnees, service):
    # Format reçu: "LIST email@domain.com"
            parties = donnees.split()
            if len(parties) >= 2:
                destinataire = parties[1]
                dictionnaire_mails = charger_boite_mail(destinataire)
                if dictionnaire_mails is not None:
                    liste_mail = commande_list(dictionnaire_mails)
                    service.sendall(f"{liste_mail}\r\n".encode('utf-8'))
                else:
                    service.sendall("501 Boîte mail inexistante\r\n".encode('utf-8'))
            else:
                service.sendall("501 Erreur syntaxe\r\n".encode('utf-8'))

def facto_retr(donnees, service):
     # Format reçu: "RETR indice email@domain.com"
            parties = donnees.split()
            if len(parties) >= 3 and parties[1].isdigit():
                indice_msg = int(parties[1])
                destinataire = parties[2]
                dictionnaire_mails = charger_boite_mail(destinataire)
                
                if dictionnaire_mails is None:
                    service.sendall("501 Boîte mail inexistante\r\n".encode('utf-8'))
                elif not validation_id(indice_msg, dictionnaire_mails):
                    service.sendall("501 ID message inexistant\r\n".encode('utf-8'))
                else:
                    message = commande_retr(dictionnaire_mails, indice_msg)
                    service.sendall(f"{message}\r\n".encode('utf-8'))
            else:
                service.sendall("501 Erreur syntaxe. Format: RETR indice email@domain.com\r\n".encode('utf-8'))


# ================================= Partie Commandes POP3 ==============================================

def commande_stat( dictionnaire_mails):
    nombre_messages = len(dictionnaire_mails)
    taille_totale = 0
    for id in dictionnaire_mails:
        taille_totale += dictionnaire_mails[id]['taille']
    return nombre_messages, taille_totale

def commande_list(dictionnaire_mails):
    # Retourne ID, expéditeur et taille
    liste_messages = [[id, dictionnaire_mails[id].get('expediteur', 'Inconnu'), dictionnaire_mails[id]['taille']] for id in dictionnaire_mails]
    return liste_messages

def commande_retr(dictionnaire_mails, id):
    return dictionnaire_mails[id]['contenu']



# Partie Vérification 
def validation_email(email, dictionnaire_mails):
    return email in dictionnaire_mails  
    
def validation_id(id, dictionnaire_mails):
    return id in dictionnaire_mails
        

# Dictionnaire_mails est un dictionnaire de dictionnaires. La clé du dictionnaire principal est l'id du destinataire et la
#  valeur est un dictionnaire contenant les messages et la taille du message
def charger_boite_mail(adresse_mail):
    # Récupère les mails pour une adresse spécifique
    chemin_fichier = os.path.join(DOSSIER_MAIL, f"{adresse_mail}.txt")
    if not os.path.exists(chemin_fichier):
        # L'adresse mail n'existe pas
        return None
    boite_mail = {}
    with open(chemin_fichier, 'r', encoding='utf-8') as f:
        contenu_complet = f.read()
    # Sépare les mails par le délimiteur
    messages = contenu_complet.split("="*50)
    
    id_mail = 1
    # Traite tous les messages sauf le dernier (qui est vide après le split)
    for message in messages[:-1]:
        # Calcule la taille avant le nettoyage
        taille = len(message.encode('utf-8'))
        message_nettoye = message.strip()
        
        # Extrait l'expéditeur de la ligne "De: ..."
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


# Partie Main
if __name__ == "__main__":
    print("=== Serveur SMTP - Démarrage du serveur === (ctrl+C pour arrêter)\n")
    try:
        initialisation_serveur()
    except KeyboardInterrupt:
        stop_server = True
        print("\n>>> Arrêt demandé. Fermeture du serveur...(après que chaque thread ait terminé)\n")