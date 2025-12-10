import threading
import time
import os
import socket

"""
Auteurs       : Bohy, Abbadi, Cheraf (et les noms de ton trinôme si applicable)
Promotion     : M1 STRI     Date          : Décembre 2025       Version       : 1.0 (SMTP Simple)

DESCRIPTION :
Ce programme implémente un serveur de messagerie électronique basique respectant
une partie du protocole SMTP (Simple Mail Transfer Protocol - RFC 5321).

FONCTIONNALITÉS (VERSION 1) :
   Architecture Serveur TCP Multithreadé :
     Socket d'écoute sur le port 2525
     Gestion de chaque client dans un thread dédié  pour permettre des connexions simultanées sans blocage.

   Gestion des commandes SMTP :
     MAIL FROM : Identification de l'expéditeur.
     RCPT TO   : Identification du destinataire.
     DATA      : Réception du corps du message (terminé par un point '.').
     QUIT      : Clôture propre de la connexion.

   Stockage :
     Les courriels reçus sont sauvegardés dans des fichiers textes locaux, le nom du fichier correspond à l'adresse du destinataire (RCPT).

UTILISATION :
Lancer ce script, puis se connecter via un client Telnet ou le script de test automatisé fourni :
$ telnet localhost 65434
"""

# Configuration des valeurs de base
HOTE = ''
PORT = 65434
DOSSIER_MAIL = 'Boîte_mail'



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
    
        while True:
            # Etape 3 : attente et acceptation d'une nouvelle connexion
            service, addr = ecoute.accept()

            # Dès que l'on accepte une connexion, on crée un thread pour gérer ce client
            thread_serveur = threading.Thread(target=gestion_client, args=(service, addr))
            thread_serveur.start()

    # Etape 5 : fermeture socket de service
    # (automatiquement par le with service)
# Etape 6 : fermeture de la socket d'écoute
# (automatiquement par le with ecoute)

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
        if (mode_data==False):
            expediteur,destinataire,mode_data,contenu_message,Condition_fin_connection=gestion_commandes(donnees,service,expediteur,destinataire,mode_data,contenu_message)
            print(f"[{adresse}] Etat après commande: expediteur={expediteur}, destinataire={destinataire}, mode_data={mode_data}")
        
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
        # Cas MAIL FROM:<adresse>
        case "MAIL":
            if "FROM:" in donnees.upper():
                expediteur = donnees.split("FROM:",1)[1].strip().strip('<>')
                service.sendall(b"250 Sender OK\r\n")
            else:
                service.sendall(b"501 Erreur syntaxe\r\n")
        
        case "RCPT":
            if "TO:" in donnees.upper():
                destinataire = donnees.split("TO:",1)[1].strip().strip('<>')
                service.sendall(b"250 Recipient OK\r\n")
            else:
                service.sendall(b"501 Erreur syntaxe\r\n")
        
        case "DATA":
            service.sendall(b"354 Enter mail, end with '.' on a line by itself \r\n")
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
    print("=== Serveur SMTP - Démarrage du serveur ===\n")
    initialisation_serveur()






