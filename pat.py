import sys
import time
import pandas as pd

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QMainWindow, QStackedWidget,QSizePolicy, QComboBox, QCheckBox, QSlider, QRadioButton, QFileDialog, QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView
from PyQt5.QtCore import QEvent, Qt, QSize, QRect, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.errorhandler import TimeoutException

import mysql.connector
import keyring

### Chrome Webdriver initialisieren ###
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-extensions")
options.add_argument("--disable-web-security")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Starte den Chrome Webdriver
driver = webdriver.Chrome(options=options)

### Verbindung zur Datenbank herstellen ###

# Establish a connection to the MySQL database
cnx = mysql.connector.connect(
  host="sql7.freemysqlhosting.net",
  user="sql7652773",
  password="edXuG1adnR",
  database="sql7652773"
)
cursor = cnx.cursor()
table_name = "PAT_Keys"
query = f"SELECT * FROM {table_name}"
cursor.execute(query)
rows = cursor.fetchall()  # Fetch all rows

keys= pd.DataFrame(rows)
keys.rename(columns={0: "ID", 1: "Partner", 2: "Key"}, inplace=True)
print(keys)

### Establish keyring ids ###
service_id_key = 'PAT_K'
service_id_pass = 'PAT_P'
service_id_user = 'PAT_U'
MAGIC_USERNAME_KEY = 'PAT_VA'

# Test Thread
class AlgorithmThread(QThread):
    """
    Dieser Thread wird für die Ausführung des Algorithmus im Hintergrund verwendet.
    """
    update_progress = pyqtSignal(int)

    def run(self):
        for i in range(21):
            time.sleep(1)  # Simuliere Algorithmus-Laufzeit mit sleep
            self.update_progress.emit(i)  # Aktualisiere den Fortschritt

# Login Screen
class LoginScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.notificationLabelPresent = False
        self.initUI()
        
    def initUI(self):        
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
                font-size: 35px;
            }
        """)
        
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignCenter)
        
        # Container für Login-Widgets
        self.loginWidget = QWidget(self)
        self.loginLayout = QVBoxLayout(self.loginWidget)
        self.loginWidget.setLayout(self.loginLayout)
        self.layout().addWidget(self.loginWidget)
        
        titleLayout = QVBoxLayout()
        title = QLabel('PAT - Prospecting Automation Tool')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        # Stellen Sie die Schriftart ein, indem Sie QFont verwenden
        font = QFont('TA Modern Times', QFont.Bold) # Ersetzen Sie 'TA Modern Times' durch den Namen einer auf Ihrem System installierten Schriftart
        title.setFont(font)
        titleLayout.addWidget(title)
        self.loginLayout.addLayout(titleLayout)
        
        # Layout für die Eingabefelder
        
        self.formLayout = QVBoxLayout()
        
        # Key, Benutzername, Passwort Eingabefelder
        self.keyInput = QLineEdit()
        self.keyInput.setPlaceholderText('Key')
        self.keyInput.setMaximumWidth(int(self.width() - 100))
        self.applyShadow(self.keyInput)

        self.userInput = QLineEdit()
        self.userInput.setPlaceholderText('Benutzername')
        self.userInput.setMaximumWidth(int(self.width() - 100))
        self.applyShadow(self.userInput)

        self.passInput = QLineEdit()
        self.passInput.setPlaceholderText('Passwort')
        self.passInput.setMaximumWidth(int(self.width() - 100))
        self.passInput.setEchoMode(QLineEdit.Password)
        self.applyShadow(self.passInput)
        
        self.notificationLabel = QLabel()
        self.notificationLabel.setAlignment(Qt.AlignCenter)
        self.notificationLabel.setStyleSheet("background-color: none; border: none; color: red;")

        # Login-Button
        self.loginButton = QPushButton('Login')
        self.loginButton.setMaximumWidth(int(self.width() - 100))
        self.loginButton.clicked.connect(self.login)
        self.loginButton.setCursor(Qt.PointingHandCursor)
        self.applyShadow(self.loginButton)
        
        # Einfügen der Widgets in das Form-Layout
        
        self.formLayout.addWidget(self.keyInput)
        self.formLayout.addWidget(self.userInput)
        self.formLayout.addWidget(self.passInput)
        self.formLayout.addWidget(self.loginButton)
        # formLayout.addWidget(self.notificationLabel)
        self.formLayout.setAlignment(Qt.AlignCenter)
        
        # Powered by CVR Media
        self.textLabel = QLabel("powered by")
        self.textLabel.setAlignment(Qt.AlignCenter)
        self.textLabel.setStyleSheet("background-color: none; border: none; color: black;")
        
        # Bild-Label
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setStyleSheet("background-color: none; border: none; color: black;")
        pixmap = QPixmap('images/cvr.png')  # Pfad zu deinem Bild
        self.imageLabel.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Footer Label
        self.footerLabel = QLabel('© Developed by Ved Antigen IT Services')
        self.footerLabel.setAlignment(Qt.AlignCenter)
        self.footerLabel.setStyleSheet("border: 10px solid #333A73; border-radius: 15px; padding: 5px")
        self.footerLabel.setMinimumHeight(100)
        self.footerLabel.setObjectName("footerLabel")

        self.loginLayout.addLayout(self.formLayout)
        self.loginLayout.addWidget(self.textLabel)
        self.loginLayout.addWidget(self.imageLabel)
        self.loginLayout.addWidget(self.footerLabel)
    
    def login(self):
        
        # Überprüfen Sie, ob die Eingabefelder nicht leer sind
        if self.keyInput.text() == "" or self.userInput.text() == "" or self.passInput.text() == "":
            print("Bitte füllen Sie alle Felder aus!")
            self.formLayout.addWidget(self.notificationLabel)
            self.notificationLabelPresent = True
            self.notificationLabel.setText("Bitte füllen Sie alle Felder aus!")
            return
        else:
            # Speichern der eingegebenen Daten in Variablen
            key = self.keyInput.text()
            username = self.userInput.text()
            password = self.passInput.text()
            
            if (keys["Partner"]==username).any():    
                
                keyring.set_password(service_id_pass, MAGIC_USERNAME_KEY, password)
                keyring.set_password(service_id_user, MAGIC_USERNAME_KEY, username)
                
                try:
        
                    driver.get("https://era.wice-net.de")
                    
                    searchLMM = driver.find_element(By.PARTIAL_LINK_TEXT, "Login mit Mandantennamen")
                    searchLMM.click()
                    search_mandant = driver.find_element(By.ID, "input_0")
                    search_mandant.send_keys("era")
                    search_email = driver.find_element(By.ID, "input_2")
                    search_email.send_keys(username)                                                                 ### Benutzernamen eingeben
                    search_passwort = driver.find_element(By.ID, "input_4")
                    search_passwort.send_keys(password)                                                                  ### Passwort eingeben
                    search_trust = driver.find_element(By.XPATH, "/html/body/div/form/div/div[2]/div/div[10]/input[1]")
                    search_trust.click()
                    
                    time.sleep(3)
                    
                    driver.switch_to.parent_frame()
                    driver.switch_to.frame("frame_menu")
                    
                    XPATH = "/html/body/form/div/ul/li[11]"
                    
                    tester = driver.find_element(By.XPATH, XPATH)
                
                    self.parent().setCurrentIndex(1)
                        
                except: 
                    
                    search_mandant.clear()
                    search_email.clear()
                    search_passwort.clear()
                    
                    if self.notificationLabelPresent:
                        self.notificationLabel.setText("Falsche Anmeldedaten!")
                    else:
                        self.formLayout.addWidget(self.notificationLabel)
                        self.notificationLabel.setText("Falsche Anmeldedaten!")
                        
            else:
                if self.notificationLabelPresent:
                    self.notificationLabel.setText("Falscher Pat-Key oder Username!!!")
                else:
                    self.formLayout.addWidget(self.notificationLabel)
                    self.notificationLabel.setText("Falscher Pat-Key oder Username!!!")
    
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 60))
        widget.setGraphicsEffect(shadow)

# Choose Screen
class ChooseScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
        """)

        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Wähle nun aus, ob du neue Prospects claimen oder bereits geclaimte Prospects unclaimen möchtest:')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        mainLayout.addWidget(title)
        
        buttonlayout = QHBoxLayout()
        claimButton = QPushButton("Claim")
        unclaimButton = QPushButton("Unclaim")
        claimButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        unclaimButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        claimButton.clicked.connect(self.claim)
        unclaimButton.clicked.connect(self.unclaim)
        self.applyShadow(claimButton)
        self.applyShadow(unclaimButton)

        buttonlayout.addWidget(claimButton)
        buttonlayout.addWidget(unclaimButton)
        buttonlayout.setSpacing(5)
        
        mainLayout.addLayout(buttonlayout)
        
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 60))
        widget.setGraphicsEffect(shadow)
        
    class AutomationThread(QThread):
        progressUpdated = pyqtSignal(int)
        finished = pyqtSignal()

        def run(self):
            for i in range(101):  # Simuliere Fortschritt
                self.progressUpdated.emit(i)  # Aktualisiere Fortschritt
                self.msleep(100)  # Warte 100ms für Demonstration
            self.finished.emit()  # Signalisiere Fertigstellung
    
    class selenium_Worker_closed(QThread):
        
    #     progress = pyqtSignal(int)
    #     finished = pyqtSignal()
        
    #     def run(self):
        
    #         try:
    #             self.driver.switch_to.parent_frame()
    #             self.progress.emit(10)  # Annahme: 10% Fortschritt

    #             self.driver.switch_to.frame("frame_menu")
    #             search_address = self.driver.find_element(By.ID, "button_plugins")
    #             search_address.click()
    #             self.progress.emit(30)  # Annahme: 30% Fortschritt

    #             self.driver.switch_to.parent_frame()
    #             self.driver.switch_to.frame("frame_main")
    #             search_search = self.driver.find_element(By.XPATH, "/html/body/div[1]")  # Switch Admin (2) und Licensee (1)
    #             search_search.click()
    #             self.progress.emit(50)  # Annahme: 50% Fortschritt

    #             XPATH = "/html/body/form/table[3]/tbody/tr/td/input[3]"

    #             try:
    #                 elem = WebDriverWait(driver, 10).until(
    #                 EC.presence_of_element_located((By.XPATH, XPATH)))
    #                 self.progress.emit(70)  # Annahme: 70% Fortschritt

    #             finally:
    #                 search_go = driver.find_element(By.XPATH, XPATH)
    #                 search_go.click()
    #                 self.progress.emit(100)  # Annahme: 100% Fortschritt
    #                 self.finished.emit()  # Senden eines Erfolgs

    #         except Exception as e:
    #             self.finished.emit(False, str(e))  # Senden eines Fehlerschlags
        pass
    
    
    def claim(self):
        print("Wechsel zu Loading-Screen")
        self.parent().setCurrentIndex(8)
            
    def unclaim(self):
        print("Wechsel zu Unclaim Screen")
        self.parent().setCurrentIndex(6)

# Search Screen
class SearchScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #50C4ED;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid #333A73;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QComboBox {
                padding: 20px;
                background-color: #FFFFFF;
                font-size: 20px;
                margin: 5px;
                border: 2px solid #333A73;
                border-radius: 15px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
        """)

        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Wähle nun die Suchkriterien für deine neuen Prospects aus:')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        # titleLayout.addWidget(title)
        mainLayout.addWidget(title)

        formLayout = QVBoxLayout()
        
        # Umsatz Eingabefeld
        revenueLayout = QHBoxLayout()
        revenueLabel = QLabel('Umsatz (in Mio.):')
        revenueMin = QLineEdit()
        revenueMin.setPlaceholderText('Von')
        self.applyShadow(revenueMin)
        revenueMax = QLineEdit()
        revenueMax.setPlaceholderText('Bis')
        self.applyShadow(revenueMax)
        revenueLayout.addWidget(revenueLabel)
        revenueLayout.addWidget(revenueMin)
        revenueLayout.addWidget(revenueMax)
        formLayout.addLayout(revenueLayout)

        # Mitarbeiter Eingabefeld
        employeeLayout = QHBoxLayout()
        employeeLabel = QLabel('Mitarbeiter:')
        employeeMin = QLineEdit()
        employeeMin.setPlaceholderText('Von')
        self.applyShadow(employeeMin)
        employeeMax = QLineEdit()
        employeeMax.setPlaceholderText('Bis')
        self.applyShadow(employeeMax)
        employeeLayout.addWidget(employeeLabel)
        employeeLayout.addWidget(employeeMin)
        employeeLayout.addWidget(employeeMax)
        formLayout.addLayout(employeeLayout)

        # Region Dropdown
        regionLayout = QHBoxLayout()
        regionLabel = QLabel('Region:')
        regionDropdown = QComboBox()
        regionDropdown.addItems(['---', 'Europa', 'Asien', 'Nordamerika'])
        # Passe größe der Auswahl an, sodass die Element Schriftgröße größer ist
        regionDropdown.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.applyShadow(regionDropdown)
        regionLayout.addWidget(regionLabel)
        regionLayout.addWidget(regionDropdown)
        formLayout.addLayout(regionLayout)

        # Zuletzt geclaimed Dropdown
        claimedLayout = QHBoxLayout()
        claimedLabel = QLabel('Zuletzt geclaimed:')
        claimedDropdown = QComboBox()
        claimedDropdown.addItems(['---', 'Noch nie gelaimed', 'Vor 1 Woche', 'Vor 2 Wochen', 'Vor 3 Wochen', 'Vor 4 Wochen'])
        self.applyShadow(claimedDropdown)
        claimedLayout.addWidget(claimedLabel)
        claimedLayout.addWidget(claimedDropdown)
        formLayout.addLayout(claimedLayout)

        # Branchen Dropdown
        industryLayout = QHBoxLayout()
        industryLabel = QLabel('Branche:')
        industryDropdown = QComboBox()
        industryDropdown.addItems(['---', 'Automotive', 'Finanzen', 'Gesundheit', 'Technologie'])
        self.applyShadow(industryDropdown)
        industryLayout.addWidget(industryLabel)
        industryLayout.addWidget(industryDropdown)
        formLayout.addLayout(industryLayout)
        
        formLayout.setSpacing(5)
        mainLayout.addLayout(formLayout)

        buttonsLayout = QHBoxLayout()
        backButton = QPushButton('Zurück')
        nextButton = QPushButton('Weiter')
        backButton.setMinimumHeight(55)
        nextButton.setMinimumHeight(55)
        self.applyShadow(backButton)
        self.applyShadow(nextButton)
        buttonsLayout.addWidget(backButton)
        buttonsLayout.addWidget(nextButton)
        buttonsLayout.setSpacing(5)
        nextButton.clicked.connect(self.weiter)
        mainLayout.addLayout(buttonsLayout)
        mainLayout.setSpacing(75)
        
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 60))
        widget.setGraphicsEffect(shadow)
        
    def weiter(self):
        print("Weiter geklickt")
        self.parent().setCurrentIndex(3)
        
    def back(self):
        print("Zurück geklickt")
        self.parent().setCurrentIndex(1)

#Claim Screen        
class ClaimScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #50C4ED;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid #333A73;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QComboBox {
                padding: 20px;
                background-color: #FFFFFF;
                font-size: 20px;
                margin: 5px;
                border: 2px solid #333A73;
                border-radius: 15px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
            QRadioButton {
                font-size: 20px;
            }
            Qslider {
                font-size: 20px;
            }
        """)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Es wurden 500 Prospects gefunden! Wähle nun wie viele geclaimt werden sollen:')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        titleLayout.addWidget(title)
        
        # Slider Layout mit Label und Slider
        
        self.sliderLayout = QHBoxLayout()
        self.sliderLabel = QLabel('Anzahl der Prospects:')
        self.sliderLabel.setMinimumHeight(75)
        self.sliderLabel.setMaximumHeight(75)
        
        # Slider zur Auswahl der Anzahl der Prospects
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)
        self.slider.valueChanged.connect(self.slider_value_changed)
        
        self.value_label = QLabel('0')  # Initialisiert das Label mit dem Startwert
        self.value_label.setMinimumHeight(75)
        self.value_label.setMaximumHeight(75)
        
        self.sliderLayout.addWidget(self.sliderLabel)
        self.sliderLayout.addWidget(self.slider)
        self.sliderLayout.addWidget(self.value_label)
        
        middleTitleLayout = QVBoxLayout()
        middleTitle = QLabel('Wähle nun welcher Status eingetragen werden soll und was als Vorgangsaktion eingetragen werden soll:')
        middleTitle.setObjectName('title')
        middleTitle.setAlignment(Qt.AlignCenter)
        middleTitle.setMinimumHeight(100)
        middleTitleLayout.addWidget(middleTitle)
        
        # Layout für Status und Vorgangsaktion
        
        self.formLayout = QVBoxLayout()
        
        # Status Dropdown
        
        self.dropdownLayout = QHBoxLayout()
        status_label = QLabel('Status')
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(['---', 'Kontaktiert', 'Nicht kontaktiert', 'Interessiert'])
        self.applyShadow(self.status_dropdown)
        self.dropdownLayout.addWidget(status_label)
        self.dropdownLayout.addWidget(self.status_dropdown)

        # Eingabefeld für Vorgangsaktion
        
        action_layout = QHBoxLayout()
        action_label = QLabel('Vorgangsaktion')
        self.action_text = QLineEdit()
        self.applyShadow(self.action_text)
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.action_text)

        # Radio Buttons
        
        # Layout für die Radio Buttons
        self.radio_layout = QHBoxLayout()
        self.check_before_claim_label = QLabel('Vor dem Claim überprüfen')
        self.check_before_claim_label.setMinimumHeight(75)
        self.check_before_claim = QRadioButton()
        self.check_before_claim.setChecked(True)
        self.use_recommended_selection_button_label = QLabel('Empfohlene Selektion nutzen')
        self.use_recommended_selection_button = QRadioButton()
        self.radio_layout.addWidget(self.check_before_claim_label)
        self.radio_layout.addWidget(self.check_before_claim)
        self.radio_layout.addWidget(self.use_recommended_selection_button_label)
        self.radio_layout.addWidget(self.use_recommended_selection_button)
        
        self.formLayout.addLayout(self.dropdownLayout)
        self.formLayout.addLayout(action_layout)
        self.formLayout.addLayout(self.radio_layout)
        
        # Buttons
        self.start_button = QPushButton('Starten')
        self.applyShadow(self.start_button)
        self.back_button = QPushButton('Zurück')
        self.applyShadow(self.back_button)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.back_button)
        buttons_layout.addWidget(self.start_button)
        
        # Anordnung der Widgets
        main_layout.addLayout(titleLayout)
        main_layout.addLayout(self.sliderLayout)
        main_layout.addLayout(middleTitleLayout)
        main_layout.addLayout(self.formLayout)
        main_layout.addLayout(buttons_layout)

        # Set the layout to the main window
        self.setLayout(main_layout)
        self.setWindowTitle('Prospecting Automation Tool')

        # Verbinden der Widgets mit Funktionen
        self.setup_connections()

    def setup_connections(self):
        # Hier könnten Signale mit Slots verbunden werden
        self.start_button.clicked.connect(self.on_start_clicked)
        self.back_button.clicked.connect(self.on_back_clicked)
        # usw.

    def on_start_clicked(self):
        # Logik, die ausgeführt wird, wenn der Start-Button geklickt wird
        print('Start wurde geklickt')
        self.parent().setCurrentIndex(4)

    def on_back_clicked(self):
        # Logik, die ausgeführt wird, wenn der Zurück-Button geklickt wird
        print('Zurück wurde geklickt')
        self.parent().setCurrentIndex(2)
        
    def slider_value_changed(self):
        self.value_label.setText(str(self.slider.value()))
        
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 60))
        widget.setGraphicsEffect(shadow)
        
# Finish Screen
class FinishScreen(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #50C4ED;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid #333A73;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QComboBox {
                padding: 20px;
                background-color: #FFFFFF;
                font-size: 20px;
                margin: 5px;
                border: 2px solid #333A73;
                border-radius: 15px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
        """)
        
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Es wurden 20 neue Prospects geclaimt!')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        titleLayout.addWidget(title)
        mainLayout.addLayout(titleLayout)
        
        # Weitere Prospects Button
        
        moreButton = QPushButton('Weitere Prospects claimen')
        moreButton.setMaximumWidth(int(self.width() - 25))
        moreButton.setMinimumWidth(int(self.width() - 25))
        self.applyShadow(moreButton)
        mainLayout.addWidget(moreButton)
        mainLayout.setAlignment(moreButton, Qt.AlignCenter)
        moreButton.clicked.connect(self.more)
        
        middleTitleLayout = QVBoxLayout()
        middleTitle = QLabel('Wenn Du die Ansprechpartner deiner soeben geclaimten Prospects exportieren möchtest, solltest du dies NUR tun, wenn Du HEUTE auschließlich Prospects der SELBEN Branche gelaimt hast, da es sonst zu Fehlern in der Zuordnung kommt!')
        # enable multiline text
        middleTitle.setWordWrap(True)
        middleTitle.setObjectName('title')
        middleTitle.setAlignment(Qt.AlignCenter)
        middleTitle.setStyleSheet("background-color: #387ADF")
        middleTitle.setMinimumHeight(100)
        middleTitleLayout.addWidget(middleTitle)
        mainLayout.addLayout(middleTitleLayout)
        
        # Ansprechpartner exportieren Button
        
        exportButton = QPushButton('Ansprechpartner exportieren')
        exportButton.setMaximumWidth(int(self.width() - 25))
        exportButton.setMinimumWidth(int(self.width() - 25))
        self.applyShadow(exportButton)
        # adjust the position of the button
        mainLayout.addWidget(exportButton)
        mainLayout.setAlignment(exportButton, Qt.AlignCenter)
        # mainLayout.setSpacing(75)
        exportButton.clicked.connect(self.export)
        
        # Zurück-Button
        
        backButton = QPushButton('Zurück')
        self.applyShadow(backButton)
        mainLayout.addWidget(backButton)
        backButton.clicked.connect(self.back)
               
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
        
    def more(self):
        print("Weitere Prospects claimen")
        self.parent().setCurrentIndex(2)
        
    def export(self):
        print("Ansprechpartner exportieren")
        self.parent().setCurrentIndex(5)
        
    def back(self):
        print("Zurück geklickt")
        self.parent().setCurrentIndex(1) 

# Export Screen
class ExportScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #50C4ED;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid #333A73;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QComboBox {
                padding: 20px;
                background-color: #FFFFFF;
                font-size: 20px;
                margin: 5px;
                border: 2px solid #333A73;
                border-radius: 15px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
        """)
        
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Wähle nun aus welchen Zeitraum PAT deine Ansprechpartner wählen soll! Außerdem wurde soeben eine neue Datei für dich gedownloadet! Bitte wähle diese aus, sie befindet sich in deinem Downloads-Ordner! Klicke anschließend auf den \"Weiter\"-Button, sodass PAT die Datei einlesen kann:')
        title.setWordWrap(True)
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        titleLayout.addWidget(title)
        mainLayout.addLayout(titleLayout)
        
        # Layout für die Eingabefelder
        
        self.formLayout = QVBoxLayout()
        
        # Öffne Datei Button
        
        self.fileButton = QPushButton('Datei öffnen')
        self.fileButton.setMaximumWidth(int(self.width() - 25))
        self.fileButton.setMinimumWidth(int(self.width() - 25))
        self.applyShadow(self.fileButton)
        self.fileButton.clicked.connect(self.openFileDialog)
        self.formLayout.addWidget(self.fileButton)
        
        # "Geclaimt vor"-Dropdown
        
        claimedLayout = QHBoxLayout()
        claimedLabel = QLabel('Geclaimt vor:')
        claimedDropdown = QComboBox()
        claimedDropdown.addItems(['---', 'Heute', 'Gestern', 'Vorgestern'])
        self.applyShadow(claimedDropdown)
        claimedLayout.addWidget(claimedLabel)
        claimedLayout.addWidget(claimedDropdown)
        claimedLayout.setSpacing(5)
        self.formLayout.addLayout(claimedLayout)
        
        self.formLayout.setSpacing(75)
        self.formLayout.setAlignment(Qt.AlignCenter)
        mainLayout.addLayout(self.formLayout)
        
        # "Weiter"- & "Zurück"-Button
        
        buttonsLayout = QHBoxLayout()
        backButton = QPushButton('Zurück')
        self.nextButton = QPushButton('Weiter')
        self.nextButton.setEnabled(False)
        self.nextButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        self.nextButton.clicked.connect(self.export)
        backButton.setMinimumHeight(55)
        self.nextButton.setMinimumHeight(55)
        self.applyShadow(backButton)
        self.applyShadow(self.nextButton)
        buttonsLayout.addWidget(backButton)
        buttonsLayout.addWidget(self.nextButton)
        buttonsLayout.setSpacing(5)
        mainLayout.addLayout(buttonsLayout)
        
        mainLayout.setAlignment(self.formLayout, Qt.AlignCenter)
        mainLayout.setSpacing(150)

    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
        
    def openFileDialog(self):
        print("Datei öffnen")
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Datei öffnen", "",
                                                  "Alle Dateien (*);;Textdateien (*.txt)", options=options)
        if fileName:
            print(fileName)
        
        # Disable the button after the file has been selected
        self.nextButton.setEnabled(True)
        self.nextButton.setStyleSheet("background-color: #387ADF; color: white;")
        # Reactivate the buttons hover effect
        self.nextButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        
    def export(self):
        print("Ansprechpartner exportieren")
        self.parent().setCurrentIndex(6)
        
    def back(self):
        print("Zurück geklickt")
        self.parent().setCurrentIndex(1)

# AP Screen
class ApScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #50C4ED;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid #333A73;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QComboBox {
                padding: 20px;
                background-color: #FFFFFF;
                font-size: 20px;
                margin: 5px;
                border: 2px solid #333A73;
                border-radius: 15px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 10px;
                border-color: #333A73;
                selection-background-color: #387ADF;
                selection-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #50C4ED;
                padding: 5px;
                border: 2px solid #333A73;
                font-size: 20px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QTableWidget QScrollBar:vertical {
                border: 2px solid #333A73;
                background: #FFFFFF;
            }
            QTableWidget QScrollBar::handle:vertical {
                background: #387ADF;
            }
            QTableWidget QScrollBar::add-line:vertical, QTableWidget QScrollBar::sub-line:vertical {
                border: 2px solid #333A73;
                background: #387ADF;
            }
        """)
        
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Wähle nun aus welche der unten aufgeführten Funktionen die APS im Unternehmen haben dürfen! Wähle anschließend einen Speicherort aus, damit PAT Deine neuen Ansprechpartner berechnen kann und diese dort abspeichern kann:')
        title.setWordWrap(True)
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        titleLayout.addWidget(title)
        mainLayout.addLayout(titleLayout)
        
        # Weitere Ansprechpartner Button
        
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(3)  # Angenommen, Sie haben 3 Spalten
        self.tableWidget.setHorizontalHeaderLabels(["Auswahl", "Name", "Beschreibung"])
        # disable the index column
        self.tableWidget.verticalHeader().setVisible(False)
        self.applyShadow(self.tableWidget)

        mainLayout.addWidget(self.tableWidget)
        
        # Zwei weitere Buttons im selben Design, wie bei den anderen Screens. Ein Button um den Speicherort auszuwählen und ein Button um die Berechnung zu starten. Der zweite Button sollte erst aktiviert werden, wenn der erste Button geklickt wurde.
        buttonsLayout = QHBoxLayout()
        saveButton = QPushButton('Speicherort auswählen')
        saveButton.clicked.connect(self.openFileDialog)
        self.exportButton = QPushButton('Exportieren')
        self.exportButton.setEnabled(False)
        self.exportButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        self.exportButton.clicked.connect(self.export)
        saveButton.setMinimumHeight(55)
        self.exportButton.setMinimumHeight(55)
        self.applyShadow(saveButton)
        self.applyShadow(self.exportButton)
        buttonsLayout.addWidget(saveButton)
        buttonsLayout.addWidget(self.exportButton)
        buttonsLayout.setSpacing(5)
        mainLayout.addLayout(buttonsLayout)
        
        # Ein Button um den Vorgang abzubrechen und zurück zu gehen
        
        backButton = QPushButton('Zurück')
        self.applyShadow(backButton)
        mainLayout.addWidget(backButton)
        backButton.clicked.connect(self.back)
        
        mainLayout.setSpacing(75)

        self.fillTable()
        self.resizeTable()

    def fillTable(self):
        for i in range(5):  # 5 Zeilen als Beispiel
            checkBox = QCheckBox()
            hLayout = QHBoxLayout()
            hLayout.addWidget(checkBox)
            hLayout.setAlignment(Qt.AlignCenter)
            hLayout.setContentsMargins(0,0,0,0)

            widget = QWidget()
            widget.setLayout(hLayout)

            self.tableWidget.setRowCount(i + 1)
            self.tableWidget.setCellWidget(i, 0, widget)  # Fügt die Checkbox zur ersten Spalte hinzu
            self.tableWidget.setItem(i, 1, QTableWidgetItem(f"Item {i+1}"))  # Name
            self.tableWidget.setItem(i, 2, QTableWidgetItem(f"Beschreibung {i+1}"))  # Beschreibung
            
    def resizeTable(self):
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
    
    # Methode, die aufgerufen wird, wenn der Speicherort-Button geklickt wird
    def openFileDialog(self):
        print("Speicherort auswählen")
        options = QFileDialog.Options()
        folderName = QFileDialog.getExistingDirectory(self, "Speicherort auswählen", options=options)
        if folderName:
            print(folderName)
        
        # Aktivieren des "Berechnen"-Buttons
        self.exportButton.setEnabled(True)
        self.exportButton.setStyleSheet("background-color: #387ADF; color: white;")
        self.exportButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
    
    def export(self):
        print("Berechnen")
        self.parent().setCurrentIndex(1)
    
    def back(self):
        print("Zurück geklickt")
        self.parent().setCurrentIndex(1)
        
# Unclaim Screen
class UnclaimScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-size: 20px;
                margin: 5px;
            }
            QLabel {
                background-color: #50C4ED;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid #333A73;
            }
            QLineEdit {
                border: 2px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #FFFFFF;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
            }
            QComboBox {
                padding: 20px;
                background-color: #FFFFFF;
                font-size: 20px;
                margin: 5px;
                border: 2px solid #333A73;
                border-radius: 15px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
            }
        """)
        
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('Im Folgenden wird dein Dashboard analysiert, um Prospects zu finden die entclaimt werden sollen:')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        # title.setMaximumHeight(100)
        titleLayout.addWidget(title)
        mainLayout.addLayout(titleLayout)
        
        # Es soll gewählt werden können, ob die Prospects vor dem Unclaimen noch überprüft werden sollen
        
        radioLayout = QHBoxLayout()
        checkBeforeUnclaimLabel = QLabel('Vor dem Unclaimen überprüfen')
        checkBeforeUnclaim = QRadioButton()
        # make the radio button bigger so that it is easier to click
        checkBeforeUnclaim.setMinimumHeight(200)
        checkBeforeUnclaim.setMinimumHeight(75)
        # checkBeforeUnclaim.setChecked(True)
        radioLayout.addWidget(checkBeforeUnclaimLabel)
        radioLayout.addWidget(checkBeforeUnclaim)
        radioLayout.setSpacing(25)
        mainLayout.addLayout(radioLayout)
        
        # 3 Buttons in einer Horizontalen Box: "Unclaimen", "Weiter" und "Abbrechen". Der "Weiter"-Button soll erst aktiviert werden, wenn der "Unclaimen"-Button geklickt wurde und der Radio-Button auf "Vor dem Unclaimen überprüfen" gesetzt wurde.
        
        buttonsLayout = QHBoxLayout()
        self.unclaimButton = QPushButton('Unclaimen')
        self.unclaimButton .clicked.connect(self.unclaim)
        self.nextButton = QPushButton('Weiter')
        self.nextButton.setEnabled(False)
        self.nextButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        self.nextButton.clicked.connect(self.next)
        cancelButton = QPushButton('Abbrechen')
        self.applyShadow(self.unclaimButton )
        self.applyShadow(self.nextButton)
        self.applyShadow(cancelButton)
        buttonsLayout.addWidget(self.unclaimButton )
        buttonsLayout.addWidget(self.nextButton)
        buttonsLayout.addWidget(cancelButton)
        buttonsLayout.setSpacing(5)
        mainLayout.addLayout(buttonsLayout)
        
        mainLayout.setSpacing(200)
        mainLayout.setAlignment(radioLayout, Qt.AlignCenter)
        
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
        
    def unclaim(self):
        print("Unclaimen")
        self.nextButton.setEnabled(True)
        self.nextButton.setStyleSheet("background-color: #387ADF; color: white;")
        self.nextButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        self.unclaimButton.setEnabled(False)
        self.unclaimButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        
    def next(self):
        print("Weiter geklickt")
        self.parent().setCurrentIndex(1)

# Loading Screen
class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Koldby';
                color: #333333;
            }
            QLabel, QProgressBar {
                font-size: 25px;
                margin: 5px;
                font-weight: bold;
            }
            QLabel {
                background-color: #FFFFFF;
                color: #333A73;
                padding: 5px;
                border-radius: 15px;
                border: 0px solid #333A73;
                font-size: 25px;
            }
            QPushButton {
                border: 3px solid #333A73;
                border-radius: 15px;
                padding: 20px;
                background-color: #387ADF;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333A73;
                border: 2px solid #333A73;
                
            }
            QProgressBar {
                border: 2px solid #333A73;
                border-radius: 5px;
                background-color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #387ADF;
                width: 20px;
                margin: 0.5px;
            }
            QLabel#title {
                background-color: #387ADF;
                color: #FFFFFF;
                padding: 5px;
                border-radius: 15px;
                border: 10px solid #333A73;
                font-weight: bold;
                font-size: 35px;
            }
        """)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        titleLayout = QVBoxLayout()
        title = QLabel('PAT - Prospecting Automation Tool')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(100)
        titleLayout.addWidget(title)
        
        # Layout für die mitte des Bildschirms
        
        middleLayout = QVBoxLayout()
        
        self.progressLabel = QLabel('Bitte warten währden PAT die Prospects analysiert.')
        self.progressLabel.setWordWrap(True)
        self.progressLabel.setAlignment(Qt.AlignCenter)
        self.progressLabel.setMinimumHeight(100)
        # disable the border of the label
        
        self.progressLayout = QVBoxLayout()
        
        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setValue(0)  # Startwert der Progress Bar
        self.progressBar.setRange(0, 100)  # Bereich der Progress Bar
        
        self.timerLabel = QLabel("0 Sekunden")
        self.timerLabel.setAlignment(Qt.AlignCenter)
        self.timerLabel.setMinimumHeight(100)
        
        self.progressLayout.addWidget(self.progressBar)
        self.progressLayout.addWidget(self.timerLabel)
        self.progressLayout.setSpacing(15)
        
        self.notificationLabel = QLabel("Dies kann einige Minuten dauern...")
        self.notificationLabel.setAlignment(Qt.AlignCenter)
        
        middleLayout.addWidget(self.progressLabel)
        middleLayout.addLayout(self.progressLayout)
        middleLayout.addWidget(self.notificationLabel)
        
        # Layout für Buttons. Ein Button um den Vorgang abzubrechen und zurück zu gehen und ein Button um nach dem Vorgang fortzufahren. Der "Weiter"-Button soll erst aktiviert werden, wenn der Vorgang abgeschlossen ist.
        
        buttonsLayout = QHBoxLayout()
        cancelButton = QPushButton('Abbrechen')
        self.nextButton = QPushButton('Weiter')
        self.nextButton.setEnabled(False)
        self.nextButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        cancelButton.setMinimumHeight(55)
        self.nextButton.setMinimumHeight(55)
        self.applyShadow(cancelButton)
        self.applyShadow(self.nextButton)
        buttonsLayout.addWidget(cancelButton)
        buttonsLayout.addWidget(self.nextButton)
        buttonsLayout.setSpacing(5)
        
        # Layout-Elemente hinzufügen
        main_layout.addLayout(titleLayout)
        main_layout.addLayout(middleLayout)
        main_layout.addLayout(buttonsLayout)
        main_layout.setAlignment(middleLayout, Qt.AlignCenter)
        main_layout.setSpacing(50)
        
    # Setter Methoden für die Progress Bar und den "Weiter"-Button
    # Überprüfen!!!
    
    def setRange(self, value):
        self.progressBar.setRange(0, value)
        
    def setProgress(self, value):
        self.progressBar.setValue(value)

    def taskCompleted(self):
        self.progressBar.setValue(100)
        self.progressLabel.setText("Analyse abgeschlossen.")
        self.notificationLabel.setText("Bereit zum Weitermachen.")
        self.nextButton.setEnabled(True)
    
    def setNext(self, index):
        print("Weiter geklickt")
        self.parent().setCurrentIndex(index)
    
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
        
# Haupt Fenster
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PAT - Prospecting Automation Tool')
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #FFFFFF;")

        self.stackedWidget = QStackedWidget(self)
        self.setCentralWidget(self.stackedWidget)

        self.loginScreen = LoginScreen()
        self.chooseScreen = ChooseScreen()
        self.searchScreen = SearchScreen()
        self.claimScreen = ClaimScreen()
        self.finishScreen = FinishScreen()
        self.ExportScreen = ExportScreen()
        self.ApScreen = ApScreen()
        self.unclaimScreen = UnclaimScreen()
        self.loadingScreen = LoadingScreen()

        self.stackedWidget.addWidget(self.loginScreen)
        self.stackedWidget.addWidget(self.chooseScreen)
        self.stackedWidget.addWidget(self.searchScreen)
        self.stackedWidget.addWidget(self.claimScreen)
        self.stackedWidget.addWidget(self.finishScreen)
        self.stackedWidget.addWidget(self.ExportScreen)
        self.stackedWidget.addWidget(self.ApScreen)
        self.stackedWidget.addWidget(self.unclaimScreen)
        self.stackedWidget.addWidget(self.loadingScreen)
        
        ### Hier wird der automatische Login ausgeführt
        
        # Comment out the lines below to use manual login
        
        try:
            
            # kr_key = keyring.get_password(service_id_key, MAGIC_USERNAME_KEY)
            kr_user = keyring.get_password(service_id_user, MAGIC_USERNAME_KEY)
            kr_pw = keyring.get_password(service_id_pass, MAGIC_USERNAME_KEY)
                        
            # if ((keys["Partner"]==kr_user) & (keys["Key"]==kr_key)).any():
            if (keys["Partner"]==kr_user).any():
                
                try:
        
                    driver.get("https://era.wice-net.de")
                    
                    searchLMM = driver.find_element(By.PARTIAL_LINK_TEXT, "Login mit Mandantennamen")
                    searchLMM.click()
                    search_mandant = driver.find_element(By.ID, "input_0")
                    search_mandant.send_keys("era")
                    search_email = driver.find_element(By.ID, "input_2")
                    search_email.send_keys(kr_user)                                                                 ### Benutzernamen eingeben
                    search_passwort = driver.find_element(By.ID, "input_4")
                    search_passwort.send_keys(kr_pw)                                                                  ### Passwort eingeben
                    search_trust = driver.find_element(By.XPATH, "/html/body/div/form/div/div[2]/div/div[10]/input[1]")
                    search_trust.click()
                    
                    time.sleep(3)
                    
                    driver.switch_to.parent_frame()
                    driver.switch_to.frame("frame_menu")
                    
                    XPATH = "/html/body/form/div/ul/li[11]"
                    
                    test = driver.find_element(By.XPATH, XPATH)
                
                    self.stackedWidget.setCurrentIndex(1)
                        
                except: 
                    
                    # searchLMM.click()
                    search_mandant.clear()
                    search_email.clear()
                    search_passwort.clear()
                    
        except:
            
            print("Kein Passwort gefunden!")
        
    def setCurrentIndex(self, index):
        self.stackedWidget.setCurrentIndex(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())