import socket
import re 

"""
Auteurs: Bohy, Abbadi, Cherraf 
Promotion: M1 STRI     Date  : Janvier 2026       Version : 2.0 (SMTP Simple)

DESCRIPTION :
Ce programme implémente un client SMTP basique respectant
une partie du protocole SMTP (Simple Mail Transfer Protocol - RFC 5321).

FONCTIONNALITÉS (VERSION 3.0) :
    Connexion à un serveur SMTP sur le port 65434
    Envoi de commandes SMTP :
      EHLO      : Identification du client (test - non implémenté sur le serveur).
      HELO      : Identification du client.
      MAIL FROM : Identification de l'expéditeur.
      RCPT TO   : Identification du destinataire.
      DATA      : Envoi du corps du message (terminé par un point '.').
      QUIT      : Clôture propre de la connexion.

      Ajout POP3 : 
       - QUIT : permet de fermer la connexion proprement.
       - STAT : permet d'obtenir le nombre de messages et la taille totale.
       - LIST : permet d'obtenir la liste des messages avec leur taille.
       - RETR n : permet de récupérer le message n.

    Compatibilité :
      Compatible avec les serveurs SMTP standards incluant celui du projet.
      Peut être utilisé avec Thunderbird en tant que serveur SMTP personnalisé.

"""

# Configuration
HOTE = 'localhost'
PORT = 65434

# Fonction de validation d'email simple
def valider_email(email):
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

#    Envoie une commande SMTP au serveur et affiche la réponse
def envoyer_commande(client, commande):
    print(f">> {commande}")
    #envoie de la commande au serveur
    client.sendall(f"{commande}\r\n".encode('utf-8'))
    data = client.recv(1024)
    reponse = data.decode('utf-8')
    print(f"<< {reponse.strip()}")
    return reponse

def verification_retour(reponse):
    return reponse[0]=="501"



def gestion_commande_list(retour):
    parts = retour.split()
    
    if verification_retour(parts):
        print(f" Retour impossible : {retour}\n")
        return
    elif len(parts) > 1:
        print("\n=== Liste des messages ===")
        elements = retour.split(',')
        print(f"\n{'ID':<10} | {'Expéditeur':<25} | {'Taille (octets)':<20}")
        print("-" * 60)
        try:
            for i in range(0, len(elements), 3):
                uid = elements[i].strip().strip("[").strip("]")
                expediteur = elements[i+1].strip().strip("'\"")
                taille = elements[i+2].strip().strip("[").strip("]")
                print(f"{uid:<10} | {expediteur:<25} | {taille:<20}")
        except IndexError:
            print("   (Problème de formatage des données) \n")

def gestion_commande_stat(retour):
    parts = retour.split()
    if verification_retour(parts):
        print("\n===  Retour Impossible  === \n")
        print(f"  {retour}\n")
        return
    elif len(parts) >= 2:
        print(f"\n=== Statistiques === \n")
        print(f"Nombre de messages : {parts[0]}")
        print(f"Taille totale : {parts[1]} octets\n")

def gestion_commande_retr(retour):
    parts = retour.split()
    if verification_retour(parts):
        print(f"{retour}\n")
        return
    else : 
        print("\n=== Contenu du message ===\n")
        message_lines = retour.split('\\n')
        for line in message_lines:
            print(line)
        print()

def choix_send():
    expediteur = input("Expéditeur: ")
    while not valider_email(expediteur):
        expediteur = input("Email invalide, (format : exemple@domaine.com). Expéditeur: ")

    destinataire = input("Destinataire: ")
    while not valider_email(destinataire):
        destinataire = input("Email invalide, (format : exemple@domaine.com). Destinataire: ")
        
    message = input("Message: ")
    while not message:
        print("Le message ne peut pas être vide. Veuillez saisir un message.")
        message = input("Message: ")
    return expediteur, destinataire, message
    

# Fonction principale pour envoyer un email via SMTP et interagir en POP3
def envoyer_email():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #connexion au serveur SMTP
        client.connect((HOTE, PORT))
        # Accueil serveur
        data = client.recv(1024)
        print(f"<< {data.decode('utf-8').strip()}")
        print("\n--- Début de la communication SMTP ---\n")

        # On essaie d'abord EHLO (qui devrait échouer avec 502)
        print("...Test EHLO...")
        envoyer_commande(client, "EHLO localhost")
        
        # Puis on envoie HELO (qui devrait réussir avec 250)
        print("...Test HELO...")
        envoyer_commande(client, "HELO localhost")
        
        # Interaction avec l'utilisateur pour envoyer plusieurs mails
        while True:
            print("=== Client SMTP - Envoi d'email ===\n")
            choix = input("Tapez 'send' pour envoyer un mail, 'rcv' pour recevoir des informations, 'quit' pour fermer la connexion : ").strip().lower()
            
            #cas QUIT
            if choix == "quit":
                envoyer_commande(client, "QUIT")
                break

            # Cas SMTP
            elif choix == "send":
                expediteur, destinataire, message = choix_send()

                # Envoi des commandes SMTP
                envoyer_commande(client, f"MAIL FROM:<{expediteur}>")
                envoyer_commande(client, f"RCPT TO:<{destinataire}>")
                envoyer_commande(client, "DATA")

                # Envoi du corps et terminaison DATA par un point
                print(f">> {message}")
                client.sendall(f"{message}\r\n".encode('utf-8'))
                envoyer_commande(client, ".")
                print("Mail envoyé avec succès.\n")

            # Cas POP3
            elif choix == "rcv":
                print("=== Client POP3 - Réception d'informations ===\n")
                choixmailpop3=input ("Veuillez saisir le mail de la personne que vous souhaitez consulter : ")
                while not valider_email(choixmailpop3):
                    choixmailpop3 = input("Email invalide, (format : exemple@domaine.com). Veuillez saisir le mail de la personne que vous souhaitez consulter : ")

                choixcommandepop3 = input("Veuillez choisir l'une des commandes suivantes : \n- 'stat' pour obtenir le nombre de messages et la taille totale \n" \
                "- 'list' pour obtenir la liste des messages avec leur taille\n" \
                "- 'retr n' pour récupérer le message d'indice n : ").strip().lower()

                if choixcommandepop3 == "stat":
                    retour = envoyer_commande(client, "STAT " + choixmailpop3)
                    gestion_commande_stat(retour)

                elif choixcommandepop3 == "list":
                    retour = envoyer_commande(client, "LIST " + choixmailpop3) 
                    gestion_commande_list(retour)


                elif choixcommandepop3.split()[0] == "retr":
                    partspop3 = choixcommandepop3.split() 
                    if (len(partspop3) == 2 and partspop3[1].isdigit()):
                        retour=envoyer_commande(client, f"RETR {partspop3[1]} {choixmailpop3}")
                        gestion_commande_retr(retour)
                    else:
                        print("\nUsage incorrect de RETR\n")

                else:
                    print("Commande non reconnue. Tapez 'stat', 'list' ou 'retr n'.")

            else:
                print("Commande non reconnue. Tapez 'send' ou 'quit'.")

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        try:
            client.close()
        except Exception:
            pass

if __name__ == "__main__":
    # envoi d'un email
    envoyer_email()
