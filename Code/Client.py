import socket

# Configuration
HOTE = 'localhost'
PORT = 65434

def envoyer_commande(client, commande):
    """Envoie une commande au serveur et affiche la réponse"""
    print(f">> {commande}")
    client.sendall(f"{commande}\r\n".encode('utf-8'))
    data = client.recv(1024)
    reponse = data.decode('utf-8')
    print(f"<< {reponse.strip()}")
    return reponse

def envoyer_email(expediteur, destinataire, message):
    """Envoie un email via SMTP"""
    # Étape 1 : création socket cliente + connexion
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            # Connexion au serveur
            client.connect((HOTE, PORT))
            data = client.recv(1024)
            reponse = data.decode('utf-8')
            print(f"<< {reponse.strip()}")
            
            # Étape 2 : échanges (envoi/réception)
            envoyer_commande(client, f"MAIL FROM:<{expediteur}>")
            envoyer_commande(client, f"RCPT TO:<{destinataire}>")
            envoyer_commande(client, "DATA")
            
            # Envoi du message
            print(f">> {message}")
            client.sendall(f"{message}\r\n".encode('utf-8'))
            
            # Fin du message
            envoyer_commande(client, ".")
            
            # Étape 3 : fermeture
            envoyer_commande(client, "QUIT")
            
            print("\nEmail envoyé avec succès!")
            
        except Exception as e:
            print(f"Erreur lors de l'envoi: {e}")

if __name__ == "__main__":
    # Exemple d'envoi d'email
    print("=== Client SMTP - Envoi d'email ===\n")
    
    expediteur = input("Expéditeur: ")
    destinataire = input("Destinataire: ")
    message = input("Message: ")
    
    print("\n--- Début de la communication SMTP ---\n")
    envoyer_email(expediteur, destinataire, message)
