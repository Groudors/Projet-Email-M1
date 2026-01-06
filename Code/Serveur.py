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

def initialisation_serveur():   
    # On crée le dossier de stockage des mails s'il n'existe pas
    if not os.path.exists(DOSSIER_MAIL):
        os.makedirs(DOSSIER_MAIL)

    # Etape 1 : création de la socket d'écoute
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ecoute:
        # Etape 1 suite : liaison de la socket d'écoute 
        ecoute.bind(('', PORT))
        # Etape 2 : ouverture du service
        ecoute.listen()
        ecoute.settimeout(1.0)
    
        while not stop_server:
            # Etape 3 : attente et acceptation d'une nouvelle connexion
            try:
                service, addr = ecoute.accept()
            except socket.timeout:
                continue

            # Dès que l'on accepte une connexion, on crée un thread pour gérer ce client
            thread_serveur = threading.Thread(target=gestion_client, args=(service, addr))
            thread_serveur.start()


def gestion_client(service, adresse):
    # Gère la communication avec un client SMTP

    print(f"Thread {threading.current_thread().name} : Connexion de l'adresse : {adresse}")
    
    # Envoie du message de confirmation de mise en place du service
    service.sendall(b"220 Service Ready\n")
    expediteur = None
    destinataire = None
    mode_data = False # Indique si on est en mode réception de données avec DATA
    contenu_message = []
    Condition_fin_connection=True
   
    while Condition_fin_connection:
        # On réceptionne des données du client
        data = service.recv(1024)
        if not data:
            break  # Connexion fermée par le client en cas d'erreur ou autre
        
        donnees = data.decode('utf-8').strip()
        print(f"[{adresse}] Reçu: {donnees}")
        # Si le message précédant n'était pas "DATA", on envoie dans gestion_commandes pour trouver le type de commande
        if (mode_data==False):
            expediteur,destinataire,mode_data,contenu_message,Condition_fin_connection=gestion_commandes(donnees,service,expediteur,destinataire,mode_data,contenu_message)
            print(f"[{adresse}] Etat après commande: expediteur={expediteur}, destinataire={destinataire}, mode_data={mode_data}")
        
        # Sinon, l'envoie de données et activé
        else:
            # En mode DATA, on collecte les lignes du message
            if donnees == ".":
                service.sendall(b"250 OK\r\n")
                # Fin de la saisie du message
                mode_data = False
                # Sauvegarde le message dans un fichier
                sauvegarder_message(expediteur, destinataire, contenu_message)
                contenu_message = []  # Réinitialise le contenu du message pour le prochain
            else:
                # Ajoute la ligne au contenu du message
                contenu_message.append(donnees)


            

def gestion_commandes(donnees,service,expediteur,destinataire,mode_data,contenu_message):
    commande = donnees.upper().split()[0] 
    match commande:
        # Gestion de EHLO (SMTP complexe non implémenté)
        case "EHLO":
            service.sendall(b"502 Command not implemented\r\n")

        # Gestion de HELO (SMTP implémenté)
        case "HELO":
            # On répond 250 OK
            service.sendall(b"250 Ok\r\n")
            
        # Cas MAIL FROM:<adresse>
        case "MAIL":
            if "FROM:" in donnees.upper():
                expediteur = donnees.split("FROM:",1)[1].strip().strip('<>')
                service.sendall(b"250 Sender OK\r\n")
            else:
                service.sendall(b"501 Erreur syntaxe\r\n")
        
        # Gestion reception du message
        case "RCPT":
            #On vérifie qu'il s'agit bien de "RCPT TO"
            if "TO:" in donnees.upper():
                destinataire = donnees.split("TO:",1)[1].strip().strip('<>')
                service.sendall(b"250 Recipient OK\r\n")
            else:
                service.sendall(b"501 Erreur syntaxe\r\n")
        
        # Gestion de la 
        case "DATA":
            service.sendall(b"354 Envoyez votre mail, finissez avec un '.' sur une ligne seul \r\n")
            mode_data = True
        
        case "QUIT":
            service.sendall(b"221 Closing connection\r\n")
            return expediteur,destinataire,mode_data,contenu_message,False  

        case _:
            service.sendall(b"502 Command not implemented\r\n")

    return expediteur,destinataire,mode_data,contenu_message,True    



def sauvegarder_message(expediteur, destinataire, contenu_message):
    #Sauvegarde le message dans un fichier correspondant au destinataire

    if destinataire!=None and expediteur!=None:
        fichier_mail = os.path.join(DOSSIER_MAIL, f"{destinataire}.txt")
        with open(fichier_mail, 'a', encoding='utf-8') as f:
            f.write(f"De: {expediteur}\n")
            f.write(f"Pour: {destinataire}\n")
            f.write("Message:\n")
            f.write('\n'.join(contenu_message))
            f.write("\n" + "="*50 + "\n\n")
        print(f"Message enregistré dans {fichier_mail}")


if __name__ == "__main__":
    print("=== Serveur SMTP - Démarrage du serveur === (ctrl+C pour arrêter)\n")
    try:
        initialisation_serveur()
    except KeyboardInterrupt:
        stop_server = True
        print("\n>>> Arrêt demandé. Fermeture du serveur...(après que chaque thread ait terminé)\n")






