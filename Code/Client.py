import socket

"""
Auteurs       : Bohy, Abbadi, Cherraf (et les noms de ton trinôme si applicable)
Promotion     : M1 STRI     Date          : Décembre 2025       Version       : 1.0 (SMTP Simple)

DESCRIPTION :
Ce programme implémente un client SMTP basique respectant
une partie du protocole SMTP (Simple Mail Transfer Protocol - RFC 5321).

FONCTIONNALITÉS (VERSION 1) :
    Connexion à un serveur SMTP sur le port 65434
    Envoi de commandes SMTP :
      MAIL FROM : Identification de l'expéditeur.
      RCPT TO   : Identification du destinataire.
      DATA      : Envoi du corps du message (terminé par un point '.').
      QUIT      : Clôture propre de la connexion.

"""

# Configuration
HOTE = 'localhost'
PORT = 65434

def envoyer_commande(client, commande):
    """Envoie une commande au serveur et affiche la réponse"""
    print(f">> {commande}")
    #envoie de la commande au serveur
    client.sendall(f"{commande}\r\n".encode('utf-8'))
    data = client.recv(1024)
    reponse = data.decode('utf-8')
    print(f"<< {reponse.strip()}")
    return reponse

def envoyer_email():
    """Ouvre une connexion SMTP et permet d'envoyer plusieurs mails avant QUIT."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #connexion au serveur SMTP
        client.connect((HOTE, PORT))
        # Accueil serveur
        data = client.recv(1024)
        print(f"<< {data.decode('utf-8').strip()}")
        print("\n--- Début de la communication SMTP ---\n")

        # Interaction avec l'utilisateur pour envoyer plusieurs mails
        while True:
            print("=== Client SMTP - Envoi d'email ===\n")
            choix = input("Tapez 'send' pour envoyer un mail ou 'quit' pour fermer la connexion : ").strip().lower()
            if choix == "quit":
                envoyer_commande(client, "QUIT")
                break
            elif choix == "send":
                expediteur = input("Expéditeur: ")
                destinataire = input("Destinataire: ")
                message = input("Message: ")

                # Envoi des commandes SMTP
                envoyer_commande(client, f"MAIL FROM:<{expediteur}>")
                envoyer_commande(client, f"RCPT TO:<{destinataire}>")
                envoyer_commande(client, "DATA")

                # Envoi du corps et terminaison DATA par un point
                print(f">> {message}")
                client.sendall(f"{message}\r\n".encode('utf-8'))
                envoyer_commande(client, ".")
                print("Mail envoyé dans cette session.")
            else:
                print("Commande non reconnue. Tapez 'send' ou 'quit'.")

    except Exception as e:
        print(f"Erreur de session SMTP: {e}")
    finally:
        try:
            client.close()
        except Exception:
            pass

if __name__ == "__main__":
    # envoi d'un email
    envoyer_email()
