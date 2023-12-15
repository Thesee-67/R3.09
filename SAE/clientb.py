import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import socket
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMutex, QMutexLocker, QWaitCondition, QMetaObject
import re

class IPValidationThread(QThread):
    result_ready = pyqtSignal(bool)

    def __init__(self, host):
        super(IPValidationThread, self).__init__()
        self.host = host

    def run(self):
        is_valid = self.valid_ip(self.host)
        self.result_ready.emit(is_valid)

    def valid_ip(self, host):
        try:
            # Utilisez socket.inet_pton pour vérifier si l'adresse IP est valide
            socket.inet_pton(socket.AF_INET, host)
            return True
        except socket.error:
            return False
        
class MessageSignal(QObject):
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
class MessageSignal(QObject):
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super(ConnectionDialog, self).__init__(parent)

        self.setWindowTitle("Connexion au Serveur")
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #34495E;
                color: white;
            }
            QPushButton {
                background-color: black;
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: black;
            }
        """)

        self.resize(400, 200)  # Ajuster la taille de la fenêtre

        layout = QVBoxLayout(self)

        label_ip = QLabel("Adresse IP du serveur:")
        label_ip.setStyleSheet("color: white;")
        self.ip_entry = QLineEdit(self)
        self.ip_entry.setPlaceholderText("Entrez l'adresse IP")

        label_port = QLabel("Port du serveur:")
        label_port.setStyleSheet("color: white;")
        self.port_entry = QLineEdit(self)
        self.port_entry.setPlaceholderText("Entrez le port")

        self.connect_button = QPushButton("Se Connecter", self)
        self.connect_button.clicked.connect(self.accept)

        layout.addWidget(label_ip)
        layout.addWidget(self.ip_entry)
        layout.addWidget(label_port)
        layout.addWidget(self.port_entry)
        layout.addWidget(self.connect_button)

    def is_valid_ip(self, ip):
        # Utilisez une expression régulière pour valider le format de l'adresse IP
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        return bool(ip_pattern.match(ip))
    
    def is_valid_port(self, port_text):
        if not port_text.isdigit():
            return False

        port = int(port_text)
        return 0 < port < 65536  # Le port doit être un entier entre 1 et 65535
    
    def get_connection_info(self):
        ip = self.ip_entry.text()
        port_text = self.port_entry.text()

        # Valider le format de l'adresse IP
        if not self.is_valid_ip(ip):
            return None

        # Valider le format du port
        if not self.is_valid_port(port_text):
            return None

        port = int(port_text)
        return ip, port
class ClientThread(QThread):
    def __init__(self, client_socket, message_signal, flag, wait_condition, mutex):
        super().__init__()
        self.client_socket = client_socket
        self.signal = message_signal
        self.flag = flag
        self.wait_condition = wait_condition
        self.mutex = mutex

    def run(self):
        try:
            while self.flag[0]:
                reply = self.client_socket.recv(1024).decode()
                if not reply:
                    break  # Arrêter la boucle si la connexion est fermée
                self.signal.message_received.emit(reply)

        except (socket.error, socket.timeout) as e:
            self.signal.error_occurred.emit(f"Erreur de connexion : {e}")

        finally:
            # Pause pour laisser le temps au thread principal de gérer la fermeture de la fenêtre
            self.msleep(100)

            # Signaliser à la condition d'attente que le thread se termine
            with QMutexLocker(self.mutex):  # Utilisez QMutexLocker pour garantir la libération du mutex
                self.wait_condition.wakeAll()

            self.client_socket.close()  # Fermer la socket

class TopicDialog(QDialog):
    def __init__(self, options, parent=None):
        super(TopicDialog, self).__init__(parent)

        self.setWindowTitle("Changer de Topic")
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
            }
            QLabel {
                color: white;
            }
            QComboBox {
                background-color: #34495E;
                color: white;
                min-width: 300px;
            }
            QPushButton {
                background-color: black;
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: black;
            }
        """)

        layout = QVBoxLayout(self)

        label = QLabel("Choisissez un nouveau topic:")
        label.setStyleSheet("color: white;")

        self.comboBox = QComboBox()
        self.comboBox.addItems(options)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.addWidget(label)
        layout.addWidget(self.comboBox)
        layout.addWidget(buttonBox)

    def selectedTopic(self):
        return self.comboBox.currentText()


class ProfileDialog(QDialog):
    def __init__(self, parent=None):
        super(ProfileDialog, self).__init__(parent)

        self.setWindowTitle("Créer un Profil")
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #34495E;
                color: white;
            }
            QPushButton {
                background-color: black;
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: black;
            }
        """)

        layout = QVBoxLayout(self)

        label = QLabel("Bienvenue ! Veuillez compléter votre profil.")
        label.setStyleSheet("color: white;")

        self.username_entry = QLineEdit(self)
        self.username_entry.setPlaceholderText("Entrez votre nom d'utilisateur")

        self.nom_entry = QLineEdit(self)
        self.nom_entry.setPlaceholderText("Entrez votre nom")

        self.prenom_entry = QLineEdit(self)
        self.prenom_entry.setPlaceholderText("Entrez votre prénom")

        self.identifiant_entry = QLineEdit(self)
        self.identifiant_entry.setPlaceholderText("Entrez votre identifiant")

        self.mot_de_passe_entry = QLineEdit(self)
        self.mot_de_passe_entry.setPlaceholderText("Entrez votre mot de passe")
        self.mot_de_passe_entry.setEchoMode(QLineEdit.Password)

        self.create_button = QPushButton("Créer le Profil", self)
        self.create_button.clicked.connect(self.create_profile)

        layout.addWidget(label)
        layout.addWidget(self.username_entry)
        layout.addWidget(self.nom_entry)
        layout.addWidget(self.prenom_entry)
        layout.addWidget(self.identifiant_entry)
        layout.addWidget(self.mot_de_passe_entry)
        layout.addWidget(self.create_button)

    def create_profile(self):
        username = self.username_entry.text()
        nom = self.nom_entry.text()
        prenom = self.prenom_entry.text()
        identifiant = self.identifiant_entry.text()
        mot_de_passe = self.mot_de_passe_entry.text()

        if username and nom and prenom and identifiant and mot_de_passe:
            profile_message = f"create_profile:{username}:{nom}:{prenom}:{identifiant}:{mot_de_passe}"
            self.accept()
            self.parent().client_socket.send(profile_message.encode())
        else:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")

class ClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GuiGui TChat")
        self.setGeometry(100, 100, 600, 400)
        self.showMaximized()  # Maximiser la fenêtre principale


        # Ajout de l'en-tête avec le titre et les informations sur l'application
        header_label = QLabel("<h1 style='color: white;'>GUIGUI Tchat Compagnie</h1>"
                              "<p style='color: white;'>Une application de messagerie conviviale.</p>", self)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("background-color: #3498db;")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.chat_text = QTextEdit(self)
        self.chat_text.setReadOnly(True)
        self.chat_text.setStyleSheet("background-color: #F0F0F0; color: black;")

        self.message_entry = QLineEdit(self)
        self.send_button = QPushButton("Envoyer", self)
        self.send_button.setStyleSheet("background-color: #25D366; color: white;")
        self.send_button.clicked.connect(self.send_message)

        self.change_button = QPushButton("Changer de Topic", self)
        self.change_button.setStyleSheet("background-color: #FFD600; color: black;")
        self.change_button.clicked.connect(self.change_topic)

        info_button = QPushButton(self)
        info_button.setIcon(QIcon("SAE\Image\Question.png"))  # Remplacez "information_icon.png" par le chemin de votre icône d'information
        info_button.clicked.connect(self.show_instructions)

        top_layout = QVBoxLayout()
        top_layout.addWidget(header_label)  # Ajout de l'en-tête
        top_layout.addWidget(self.chat_text)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.message_entry)
        bottom_layout.addWidget(self.send_button)
        bottom_layout.addWidget(self.change_button)
        bottom_layout.addWidget(info_button)

        layout = QVBoxLayout(self.central_widget)
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)

        self.mutex = QMutex()  # Créez un objet QMutex

        self.client_socket = socket.socket()
        self.flag = [True]
        self.wait_condition = QWaitCondition()  # Condition d'attente pour le thread
        self.receive_thread = ClientThread(self.client_socket, MessageSignal(), self.flag, self.wait_condition, self.mutex)
        self.receive_thread.signal.message_received.connect(self.handle_message)

        self.connect_to_server()

    def connect_to_server(self):
        progress_dialog = None  # Déclarer la variable en dehors de la boucle

        while True:
            connection_dialog = ConnectionDialog(self)
            result = connection_dialog.exec_()

            if result != QDialog.Accepted:
                # L'utilisateur a appuyé sur "Annuler" ou fermé la fenêtre, quitter la boucle
                break

            connection_info = connection_dialog.get_connection_info()

            if connection_info is not None:
                host, port = connection_info

                # Valider l'adresse IP dans un thread séparé
                ip_validation_thread = IPValidationThread(host)
                ip_validation_thread.result_ready.connect(self.handle_ip_validation_result)
                ip_validation_thread.start()

                # Afficher une boîte de progression pendant la vérification
                progress_dialog = QProgressDialog("Vérification en cours...", None, 0, 0, self)
                progress_dialog.setWindowModality(Qt.WindowModal)
                progress_dialog.show()

            else:
                # La validation a échoué, afficher un message si nécessaire
                continue  # Afficher à nouveau la boîte de dialogue en cas d'erreur

    def handle_ip_validation_result(self, is_valid):
        global progress_dialog  # Utiliser la variable globale
        progress_dialog.close()  # Fermer la boîte de progression
        if not is_valid:
            QMessageBox.warning(self, "Erreur", "Adresse IP invalide. Veuillez réessayer.")

        
    def valid_port(self, port):
        try:
            port = int(port)
            return 0 < port < 65536  # Le port doit être un entier entre 1 et 65535
        except ValueError:
            return False

    def show_error_dialog(self, error_message):
        self.flag[0] = False
        self.client_socket.close()

        # Utiliser QMetaObject.invokeMethod pour demander au thread principal d'afficher le message d'erreur
        QMetaObject.invokeMethod(self, "_show_error_dialog", Qt.QueuedConnection, Q_ARG(str, error_message))

    @pyqtSlot(str)
    def _show_error_dialog(self, error_message):
        # Afficher un message d'erreur depuis le thread principal
        QMessageBox.critical(None, "Erreur", error_message)


    def handle_message(self, message):
        # Gérer le message de profil
        if message.lower().startswith("profile:"):
            _, profile_info = message.split(":", 1)
            QMessageBox.information(self, "Profil", profile_info)
        else:
            self.chat_text.append(message)
            cursor = self.chat_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.chat_text.setTextCursor(cursor)

    def send_message(self):
        message = self.message_entry.text()
        self.client_socket.send(message.encode())
        self.message_entry.clear()

    def change_topic(self):
        # Créer une instance de TopicDialog
        topic_dialog = TopicDialog(["Général", "BlaBla", "Comptabilité", "Informatique", "Marketing"], self)
        result = topic_dialog.exec_()

        if result == QDialog.Accepted:
            new_topic = topic_dialog.selectedTopic()
            self.client_socket.send(f"change:{new_topic}".encode())
            self.message_entry.clear()

    def show_instructions(self):
        # Créer une instance de QMessageBox
        info_box = QMessageBox(self)

        # Appliquer le style uniquement à cette instance
        info_box.setStyleSheet("""
            QMessageBox {
                background-color: orange; /* Fond blanc */
            }
            QLabel {
                color: black;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)

        # Configurer le texte et le titre de la boîte de dialogue
        info_box.setWindowTitle("Informations")
        info_box.setText("Bienvenue sur GuiGui Tchat!<br><br>"
                        "Utilisez le bouton 'Changer de Topic' pour changer de salon du tchat.<br><br>"
                        "Quand vous recevez le message d'arrêt du serveur, veuillez fermer l'application.<br><br>"
                        "Si vous avez des problèmes, n'hésitez pas à contacter l'équipe technique via l'adresse mail suivante <a href='mailto:olivier.guittet@uha.fr'>olivier.guittet@uha.fr</a>.<br><br>"
                        "Cordialement l'équipe technique.")

        # Ajouter un bouton "OK" à la boîte de dialogue
        info_box.addButton(QMessageBox.Ok)

        # Afficher la boîte de dialogue
        info_box.exec_()

    def closeEvent(self, event):
        # Redéfinir la méthode closeEvent pour gérer la fermeture de la fenêtre
        self.flag[0] = False  # Arrêter le thread de réception
        self.client_socket.close()  # Fermer la socket

        # Attendre que le thread de réception se termine
        with QMutexLocker(self.mutex):  # Utilisez QMutexLocker pour garantir la libération du mutex
            self.wait_condition.wakeAll()
        self.receive_thread.quit()  # Ajouter cette ligne pour quitter le thread de manière propre
        self.receive_thread.wait()  # Attendre que le thread de réception se termine

        event.accept()  # Accepter la fermeture de la fenêtre

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client_gui = ClientGUI()
    client_gui.show()
    sys.exit(app.exec_())


