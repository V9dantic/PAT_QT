import sys
import time
import pandas as pd
import threading
import datetime as dt
from datetime import datetime, timedelta

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QMainWindow, QStackedWidget,QSizePolicy, QComboBox, QCheckBox, QSlider, QRadioButton, QFileDialog, QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView
from PyQt5.QtCore import QEvent, Qt, QSize, QRect, QThread, pyqtSignal, QTimer, pyqtSlot
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

### Laden der Branchen-Tabelle ###
branchen = pd.read_excel("sources/Branche_Input.xlsx", index_col=False)
print(branchen)

### Methode zum Zählen der gefundenen Prospects ###
def get_prospects(): 
    
    try:
        
        ### Surround with try

        XPATH = "/html/body/form/table[4]/tbody/tr/td"
        total = driver.find_element(By.XPATH, XPATH)

        text = total.text
        text = text.split("von")[1]
        text = text.strip()
        text = int(text)
        text = text*50

        return text

    except:
        
        return 0
    
### Clicker-Methode für das klicken von Buttons mit Selenium ###
def clicker(XPATH):
    
    try:
        elem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, XPATH)))
        
    finally:
        search_go = driver.find_element(By.XPATH, XPATH)
        search_go.click()
        
### Methode zum analysieren der Firmenbeziehungen der Prospects ###   
def mother_search(start_len, total_len, daughters, mothers, adjust):
    
    print("#####################################################################################################")
    
    repeat = False
    new_start = total_len
    
    for i in range(start_len, total_len):
        
        if i != 0:

            print("Tab #"+str(i-adjust))
            
            driver.switch_to.window(driver.window_handles[i-adjust])
            
            has_duns = False
            akt_relations = []

            XPATH = "/html/body/div[2]/form/table[1]/tbody/tr/th"
            title = driver.find_element(By.XPATH, XPATH)
            name = title.text.lstrip("Firma ")
            print("Name: " + name)
            
            XPATH="//*[@id=\"main_container\"]/form/table[3]/tbody/tr[2]/td/table/tbody/tr[1]/td[4]/table"
            table = driver.find_element(By.XPATH, XPATH)
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            ## DUNS-Nummer Suche
            
            for row in rows:
                
                if row.text.startswith("DUNS-Nummer:"):
                    
                    duns = int(''.join(filter(str.isdigit, row.text)))
                    has_duns = True
                    
            if has_duns == True and (not duns in daughters["Duns"].values):
                
                daughters = pd.concat([daughters, pd.DataFrame([[name, i-adjust, duns]], columns=["Firma", "Tab", "Duns"])], ignore_index=True)
                
                XPATH = "//*[@id=\"main_container\"]/form/table[3]/tbody/tr[2]/td/table"
                table = driver.find_element(By.XPATH, XPATH)
                sections = table.find_elements(By.TAG_NAME, "tr")
                
                for section in sections:
                    
                    if section.text.startswith("Adressbeziehungen"):
                        
                        anzahl_relations = 0
                        rows = section.find_elements(By.TAG_NAME, "tr")
                        first_time = True
                        
                        for row in rows:
                            
                            cells = row.find_elements(By.TAG_NAME, "td")
                            
                            if len(cells) > 1:
                                
                                if cells[0].text.startswith(name):
                                    
                                    if cells[1].text == "ist direkte Tochter":
                                        
                                        if cells[0].text.split("(")[0] != cells[2].text.split("(")[0]:
                                            
                                            anzahl_relations += 1
                                            link = cells[2].find_element(By.TAG_NAME, "a")
                                            link.send_keys(Keys.CONTROL + Keys.RETURN)
                                            repeat = True
                                        
                                        else:
                                            
                                            print("Same name...")    
                                    
                                elif cells[2].text.lstrip("von ").startswith(name):
                                    
                                    print("Tochterfirma")
                                    
                        add_to_len = anzahl_relations
                        current_tabs = driver.window_handles
                        
                        for j in range(anzahl_relations):
                            
                            driver.switch_to.window(driver.window_handles[total_len + j])
                            akt_relations.append(total_len + j)
                            geclaimt = False
                            
                            XPATH = "/html/body/div[2]/form/table[2]/tbody/tr/td[3]/div/span/span/a"
                            era_status = driver.find_element(By.XPATH, XPATH)
                            era_status.click()
                            
                            try: 
                                
                                XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[2]/input"
                                claim_button = driver.find_element(By.XPATH, XPATH)
                                
                            except:
                                
                                geclaimt = True
                                XPATH = "/html/body/div[2]/form/table[1]/tbody/tr/th"
                                title = driver.find_element(By.XPATH, XPATH)
                                mother_name = title.text.lstrip("Firma ")
                                XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table/tbody/tr/td[1]/div[1]"

                                status = driver.find_element(By.XPATH, XPATH)

                                XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table/tbody/tr/td[2]/div[1]"

                                partner = driver.find_element(By.XPATH, XPATH)

                                XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table/tbody/tr/td[3]/div[1]"
                                tage = driver.find_element(By.XPATH, XPATH)
                                                                
                                if status.text != "Client":

                                    tage = int(''.join(filter(str.isdigit, tage.text)))

                                    tage = datetime.today() - timedelta(days=tage)

                                    tage = tage.replace(hour=0, minute=0, second=0, microsecond=0)
                                    
                                else:
                                    
                                    tage = datetime.strptime(tage.text, '%Y-%m-%d')
                                
                                mothers = pd.concat([mothers, pd.DataFrame([[mother_name, total_len + j, True, name, partner.text, tage, status.text]], columns=["Firma", "Tab", "Geclaimt", "Tochter", "Geclaimt/Client von", "Geclaimt/Client seit", "Status"])], ignore_index=True)
                                
                                clicker("/html/body/div[2]/form/table[2]/tbody/tr/td[1]/span/span/a")
                                
                            if geclaimt == False:
                                
                                clicker("/html/body/div[2]/form/table[2]/tbody/tr/td[1]/span/span/a")
                                
                                XPATH = "/html/body/div[2]/form/table[1]/tbody/tr/th"
                                title = driver.find_element(By.XPATH, XPATH)
                                mother_name = title.text.lstrip("Firma ")
                                
                                mothers = pd.concat([mothers, pd.DataFrame([[mother_name, total_len + j, False, name]], columns=["Firma", "Tab", "Geclaimt", "Tochter"])], ignore_index=True)
                                
                        total_len += add_to_len
                            
                        driver.switch_to.window(driver.window_handles[i-adjust])
            
            else:
                
                print("Duplicate or no DUNS-number")
                driver.close()
        
                adjust += 1
                total_len = total_len - 1            

    return mothers, daughters, repeat, new_start, total_len, adjust

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
    def __init__(self, changeScreenCallback, startAutomationCallback):
        self.changeScreenCallback = changeScreenCallback
        self.startAutomationCallback = startAutomationCallback
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
        
            try:
                driver.switch_to.parent_frame()
                self.progressUpdated.emit(10)  # Annahme: 10% Fortschritt

                driver.switch_to.frame("frame_menu")
                search_address = driver.find_element(By.ID, "button_plugins")
                search_address.click()
                self.progressUpdated.emit(30)  # Annahme: 30% Fortschritt

                driver.switch_to.parent_frame()
                driver.switch_to.frame("frame_main")
                search_search = driver.find_element(By.XPATH, "/html/body/div[1]")  # Switch Admin (2) und Licensee (1)
                search_search.click()
                self.progressUpdated.emit(50)  # Annahme: 50% Fortschritt

                XPATH = "/html/body/form/table[3]/tbody/tr/td/input[3]"

                try:
                    elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, XPATH)))
                    self.progressUpdated.emit(70)  # Annahme: 70% Fortschritt

                finally:
                    search_go = driver.find_element(By.XPATH, XPATH)
                    search_go.click()
                    self.progressUpdated.emit(100)  # Annahme: 100% Fortschritt
                    self.finished.emit()  # Senden eines Erfolgs

            except Exception as e:
                self.finished.emit(False, str(e))  # Senden eines Fehlerschlags
     
    def claim(self):
        self.startAutomationCallback()  # Startet die Automation
        self.changeScreenCallback(8)
            
    def unclaim(self):
        print("Wechsel zu Unclaim Screen")
        self.parent().setCurrentIndex(7)

# Search Screen
class SearchScreen(QWidget):
    
    sendBranche = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
        self.never_claimed_pressed = False
        self.last_claimed = "---"
        self.branche_claim = "---"
        
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

        self.formLayout = QVBoxLayout()
        
        # Umsatz Eingabefeld
        revenueLayout = QHBoxLayout()
        revenueLabel = QLabel('Umsatz (in Mio.):')
        self.revenueMin = QLineEdit()
        self.revenueMin.setPlaceholderText('Von')
        self.applyShadow(self.revenueMin)
        self.revenueMax = QLineEdit()
        self.revenueMax.setPlaceholderText('Bis')
        self.applyShadow(self.revenueMax)
        revenueLayout.addWidget(revenueLabel)
        revenueLayout.addWidget(self.revenueMin)
        revenueLayout.addWidget(self.revenueMax)
        self.formLayout.addLayout(revenueLayout)

        # Mitarbeiter Eingabefeld
        employeeLayout = QHBoxLayout()
        employeeLabel = QLabel('Mitarbeiter:')
        self.employeeMin = QLineEdit()
        self.employeeMin.setPlaceholderText('Von')
        self.applyShadow(self.employeeMin)
        self.employeeMax = QLineEdit()
        self.employeeMax.setPlaceholderText('Bis')
        self.applyShadow(self.employeeMax)
        employeeLayout.addWidget(employeeLabel)
        employeeLayout.addWidget(self.employeeMin)
        employeeLayout.addWidget(self.employeeMax)
        self.formLayout.addLayout(employeeLayout)

        # Region Dropdown
        regionLayout = QHBoxLayout()
        regionLabel = QLabel('Region:')
        self.regionDropdown = QComboBox()
        self.regionDropdown.addItems(["---", "Region 1", "Region 2", "Region 3", "Region 4", "Region 5", "Region 6", "Region 7", "Region 8", "Region 9", "Region AT", "Region CH"])
        # Passe größe der Auswahl an, sodass die Element Schriftgröße größer ist
        self.regionDropdown.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.applyShadow(self.regionDropdown)
        regionLayout.addWidget(regionLabel)
        regionLayout.addWidget(self.regionDropdown)
        self.formLayout.addLayout(regionLayout)

        # Zuletzt geclaimed Dropdown
        claimedLayout = QHBoxLayout()
        claimedbeforeLayout = QHBoxLayout()
        self.claimedLabel = QLabel('Zuletzt geclaimed:')
        self.claimedDropdown = QComboBox()
        self.applyShadow(self.claimedDropdown)
        self.claimedDropdown.addItems(["---", "3 Monaten", "6 Monaten", "1 Jahr", "3 Jahren", "5 Jahren"])
        claimedbeforeLayout.addWidget(self.claimedLabel)
        claimedbeforeLayout.addWidget(self.claimedDropdown)
        claimedLayout.setSpacing(5)
        neverClaimedLayout = QHBoxLayout()
        self.neverClaimedLabel = QLabel('Noch nie gelaimed')
        self.neverClaimedBox = QCheckBox()
        neverClaimedLayout.addWidget(self.neverClaimedLabel)
        neverClaimedLayout.addWidget(self.neverClaimedBox)
        neverClaimedLayout.setSpacing(5)
        claimedLayout.addLayout(claimedbeforeLayout)
        claimedLayout.addLayout(neverClaimedLayout)
        claimedLayout.setSpacing(5)
        self.formLayout.addLayout(claimedLayout)

        # Branchen Dropdown
        industryLayout = QHBoxLayout()
        industryLabel = QLabel('Branche:')
        self.industryDropdown = QComboBox()
        self.industryDropdown.addItems(branchen["Name"].tolist())
        self.applyShadow(self.industryDropdown)
        industryLayout.addWidget(industryLabel)
        industryLayout.addWidget(self.industryDropdown)
        self.formLayout.addLayout(industryLayout)
        
        self.formLayout.setSpacing(5)
        mainLayout.addLayout(self.formLayout)

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
        
    def automationMethodSearch(self):
        
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_main")
             
        self.claimedLabel.setStyleSheet("background-color: #50C4ED;")
        self.neverClaimedLabel.setStyleSheet("background-color: #50C4ED;")
        
        # Speichern der aktuellen Auswahl des claimed-Dropdowns
        self.last_claimed = self.claimedDropdown.currentText()
        
        print(self.last_claimed)
        print(self.neverClaimedBox.isChecked())
        
        if self.neverClaimedBox.isChecked() == True and self.last_claimed != "---":
            self.claimedDropdown.setCurrentIndex(0)
            self.neverClaimedBox.setChecked(False)
            
            # Färbe das Dropdown Label und das "Noch nie geclaimed" Label rot
            self.claimedLabel.setStyleSheet("background-color: #990000;")
            self.neverClaimedLabel.setStyleSheet("background-color: #990000;")
                      
            return
        
        # Speichern der Werte der Eingabefelder
        
        min_turn = self.revenueMin.text()
        max_turn = self.revenueMax.text()
        min_emp = self.employeeMin.text()
        max_emp = self.employeeMax.text()
        
        # driver.switch_to.parent_frame()
        # driver.switch_to.frame("frame_menu")
        
        XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/input[1]"
        search_settings = driver.find_element(By.XPATH, XPATH)
        search_settings.clear()
        search_settings.send_keys(min_turn)

        XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/input[2]"
        search_settings = driver.find_element(By.XPATH, XPATH)
        search_settings.clear()
        search_settings.send_keys(max_turn)

        XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/input[1]"
        search_settings = driver.find_element(By.XPATH, XPATH)
        search_settings.clear()
        search_settings.send_keys(min_emp)

        XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/input[2]"
        search_settings = driver.find_element(By.XPATH, XPATH)
        search_settings.clear()
        search_settings.send_keys(max_emp)

        region_input = self.regionDropdown.currentText()
        
        if region_input == "---":
            
            XPATH = "//*[@id=\"address_category4\"]/option[1]"
            
        else:
            
            region_input = str(region_input.split(" ")[1])
            
            if region_input == "AT":
            
                XPATH = "//*[@id=\"address_category4\"]/option[11]"
                
            elif region_input == "CH":
            
                XPATH = "//*[@id=\"address_category4\"]/option[12]"
                
            else:
                region_input = int(region_input)+1
                XPATH = f"//*[@id=\"address_category4\"]/option[{str(region_input)}]"
        
        search_settings = driver.find_element(By.XPATH, XPATH)
        search_settings.click()
        
        # Check for the box "Noch nie geclaimed"
        if  self.neverClaimedBox.isChecked() == False:
            
            if self.never_claimed_pressed == True:
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/input"
                search_settings = driver.find_element(By.XPATH, XPATH)
                print("Hit")
                search_settings.click()
                self.never_claimed_pressed = False
            
            if self.last_claimed == "3 Monaten":
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[2]"
                
            elif self.last_claimed == "6 Monaten":
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[3]"
                
            elif self.last_claimed == "1 Jahr":
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[4]"
                
            elif self.last_claimed == "3 Jahren":
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[5]"
                
            elif self.last_claimed == "5 Jahren":
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[5]"
                
            else:
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[1]"
                
            search_settings = driver.find_element(By.XPATH, XPATH)
            print(search_settings.get_attribute("value"))
            search_settings.click()
            
        else:
            
            XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/select/option[1]"
            search_settings = driver.find_element(By.XPATH, XPATH)
            search_settings.click()
            
            if self.never_claimed_pressed == False:
                
                XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/input"
                search_settings = driver.find_element(By.XPATH, XPATH)
                search_settings.click()
                self.never_claimed_pressed = True
            
        self.branche = self.industryDropdown.currentText()
        self.sendBranche.emit(self.branche)
        
        if self.branche != "---":
        
            branche = branchen[branchen["Name"]==self.branche]
            
            left = int(branche["Branche_l"].values)
            left = str(left)
            
            right = int(branche["Branche_r"].values)
            right = right - 1
            right = str(right)

            XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[2]/table/tbody/tr[1]/td[2]/input[1]"
            search_settings = driver.find_element(By.XPATH, XPATH)
            search_settings.clear()
            search_settings.send_keys(left)

            XPATH = "//*[@id=\"available_addresses_filter_div\"]/table/tbody/tr/td[2]/table/tbody/tr[1]/td[2]/input[2]"
            search_settings = driver.find_element(By.XPATH, XPATH)
            search_settings.clear()
            search_settings.send_keys(right)

        XPATH = "/html/body/form/table[3]/tbody/tr/td/button"
        search_settings = driver.find_element(By.XPATH, XPATH)
        search_settings.click()
        
        print("Before setting the parent")
        self.parent().setCurrentIndex(3)
        print("After setting the parent")
        
    def weiter(self):
        self.methodThread = threading.Thread(target=self.automationMethodSearch)
        self.methodThread.start()
        
    def back(self):
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        clicker("/html/body/form/div/ul/li[1]")
        
        self.parent().setCurrentIndex(1)

#Claim Screen        
class ClaimScreen(QWidget):
    
    beenVisited = False
    
    def __init__(self, changeScreenCallback, startAutomationCallback):
        self.changeScreenCallback = changeScreenCallback
        self.startAutomationCallback = startAutomationCallback
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
        
        self.title = QLabel('Es wurden 500 Prospects gefunden! Wähle nun wie viele geclaimt werden sollen:')
        self.title.setObjectName('title')
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setMinimumHeight(100)
        titleLayout.addWidget(self.title)
        
        # Slider Layout mit Label und Slider
        
        self.sliderLayout = QHBoxLayout()
        self.sliderLabel = QLabel('Anzahl der Prospects:')
        self.sliderLabel.setMinimumHeight(75)
        self.sliderLabel.setMaximumHeight(75)
        
        # Slider zur Auswahl der Anzahl der Prospects
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimum(0)
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
        self.status_dropdown.addItems(["---", "A - Prospect/AP qualifiziert", "B - An Telemarketing übergeben"])
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
        # Weiter Button, der erstmal disabled ist und ausgegraut
        self.weiter_button = QPushButton('Weiter')
        self.weiter_button.setEnabled(False)
        self.weiter_button.setStyleSheet("background-color: #AAAAAA; color: white;")
        self.applyShadow(self.weiter_button)
        self.back_button = QPushButton('Zurück')
        self.applyShadow(self.back_button)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.back_button)
        buttons_layout.addWidget(self.weiter_button)
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

    def on_enter(self):
        # Setze die Hintergrundfarbe des Title-Labels zurück
        
        if self.beenVisited==False:
            self.title.setStyleSheet("background-color: #387ADF")
            # Setze die Buttons zurück
            self.weiter_button.setEnabled(False)
            self.weiter_button.setStyleSheet("background-color: #AAAAAA; color: white;")
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet("background-color: #387ADF; color: white;")
            self.start_button.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
            
            try:   
                prospects_count = get_prospects()
                
                if prospects_count == 50:
                    XPATH = "/html/body/form/table[5]"
                    table = driver.find_element(By.XPATH, XPATH)
                    elements = table.find_elements(By.TAG_NAME, "tr")
                    prospects_count = len(elements) - 1
                    
                # Setze den Text des Title-Labels
                self.title.setText(f'Es wurden {prospects_count} Prospects gefunden! Wähle nun wie viele geclaimt werden sollen:')
                
            except:
                #check if the windowhandle is still the same (#0)
                if driver.current_window_handle != driver.window_handles[0]:
                    self.title.setStyleSheet("background-color: #990000;")
                else:
                    print("Es wurden keine Prospects gefunden!")
                    self.parent().setCurrentIndex(2)
    
    def setup_connections(self):
        self.start_button.clicked.connect(self.on_start)
        self.weiter_button.clicked.connect(self.on_weiter)
        self.back_button.clicked.connect(self.on_back)
    
    def on_start(self):
        self.startAutomationCallback()  # Startet die Automation
        self.changeScreenCallback(8)
        
    def on_weiter(self):
        self.startAutomationCallback()  # Startet die Automation
        self.changeScreenCallback(8)
        self.beenVisited = False

    class AutomationThread_S(QThread):
        progressUpdated = pyqtSignal(int)
        finished = pyqtSignal(int)
        sendClaimedDf = pyqtSignal(pd.DataFrame)
        sendProspectsWithBranche = pyqtSignal(pd.DataFrame)
        
        # Konstruktor zum übergeben von Parametern
        def __init__(self, last_claimed, value_label, check_before_claim, action_text, branche):
            QThread.__init__(self)
            self.last_claimed = last_claimed
            self.value_label = value_label
            self.check_before_claim = check_before_claim
            self.action_text = action_text
            self.branche = branche
            
        def run(self):
            print("Start Thread started")
            self.prospects_geclaimt = 0
            # global claimLog
            anzahl_tabs = 0
            self.maxClaims = int(self.value_label)
            self.aktion = self.action_text
            
            XPATH= "/html/body/form/table[5]"

            table_prospects = driver.find_element(By.XPATH, XPATH)
            prospects = table_prospects.find_elements(By.TAG_NAME, "tr")
            
            if self.maxClaims == 0:
                self.finished.emit(0)
                return
            
            counter = 1
            for row in prospects:
                if anzahl_tabs == self.maxClaims:
                    break

                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    for cell in cells:
                        try:
                            tab = cell.find_element(By.TAG_NAME, "a")
                            tab.send_keys(Keys.CONTROL + Keys.RETURN)
                            anzahl_tabs = anzahl_tabs + 1
                        except:
                            print("No Link")
                except:
                    print("first row")
                
                self.progressUpdated.emit(int((counter / self.maxClaims) * 10))
                counter = counter + 1
            print(f"Es wurden {anzahl_tabs} neue Tabs geöffnet!")

            ### Hier werden veraltete Prospects rausgefiltert

            tabs = driver.window_handles
            anzahl_prospects = 0

            for i in tabs:
                driver.switch_to.window(i)

                if i != driver.window_handles[0]:
                
                    XPATH = "//*[@id=\"main_container\"]/form/table[3]/tbody/tr[2]/td/table"
                    
                    table = driver.find_element(By.XPATH, XPATH)
                    rows = table.find_elements(By.TAG_NAME, "tr")

                    for row in rows:

                        infos = row.find_elements(By.TAG_NAME, "td")

                        for info in infos:
                        
                            if info.text.startswith("DB-Eintrag"):

                                if info.text.endswith("24"):

                                    anzahl_prospects = anzahl_prospects + 1
                                            
                                else:

                                    print(info.text)
                                    driver.close()
                                    
                self.progressUpdated.emit(10 + int((anzahl_prospects / self.maxClaims) * 20))
                counter = counter + 1
            ### Nun werden Firmen mit geclaimten Müttern rausgefiltert ###
            
            tabs = driver.window_handles
            start_len = len(tabs)
            total_len = start_len

            columns_d = ["Firma", "Tab", "Duns"]
            daughters = pd.DataFrame(columns=["Firma", "Tab", "Duns"])
            daughters = daughters.reindex(columns=columns_d)

            columns_m = ["Firma", "Tab", "Geclaimt", "Tochter", "Geclaimt/Client von", "Geclaimt/Client seit", "Status"]
            mothers = pd.DataFrame(columns=["Firma", "Tab", "Geclaimt", "Tochter", "Geclaimt/Client von", "Geclaimt/Client seit", "Status"])
            mothers = mothers.reindex(columns=columns_m)
            
            columns_miss = ["Firma", "Tab", "Geclaimt", "Tochter"]

            adjust = 0

            for i in range(start_len):
                
                if i != 0:

                    print("Tab #"+str(i-adjust))
                    
                    driver.switch_to.window(driver.window_handles[i-adjust])
                    
                    has_duns = False
                    akt_relations = []

                    XPATH = "/html/body/div[2]/form/table[1]/tbody/tr/th"
                    title = driver.find_element(By.XPATH, XPATH)
                    name = title.text.lstrip("Firma ")
                    print("Name: " + name)
                    
                    XPATH="//*[@id=\"main_container\"]/form/table[3]/tbody/tr[2]/td/table/tbody/tr[1]/td[4]/table"
                    table = driver.find_element(By.XPATH, XPATH)
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    ### DUNS-Nummer Suche
                    
                    for row in rows:
                        
                        if row.text.startswith("DUNS-Nummer:"):
                            
                            duns = int(''.join(filter(str.isdigit, row.text)))
                            has_duns = True
                            
                    if has_duns == True and (not duns in daughters["Duns"].values):
                        
                        daughters = pd.concat([daughters, pd.DataFrame([[name, i-adjust, duns]], columns=columns_d)], ignore_index=True)        
                            
                        XPATH = "//*[@id=\"main_container\"]/form/table[3]/tbody/tr[2]/td/table"
                        table = driver.find_element(By.XPATH, XPATH)
                        sections = table.find_elements(By.TAG_NAME, "tr")
                        
                        for section in sections:
                            
                            if section.text.startswith("Adressbeziehungen"):
                                
                                anzahl_relations = 0
                                rows = section.find_elements(By.TAG_NAME, "tr")
                                first_time = True
                                
                                for row in rows:
                                    
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    
                                    if len(cells) > 1:
                                        
                                        if cells[0].text.startswith(name):
                                            
                                            if cells[1].text == "ist direkte Tochter":
                                                
                                                if cells[0].text.split("(")[0] != cells[2].text.split("(")[0]:
                                                
                                                    anzahl_relations += 1
                                                    link = cells[2].find_element(By.TAG_NAME, "a")
                                                    link.send_keys(Keys.CONTROL + Keys.RETURN)
                                                    
                                                else:
                                                    
                                                    print("Same name...")
                                            
                                        elif cells[2].text.lstrip("von ").startswith(name):
                                            
                                            print("Tochterfirma")
                                            
                                add_to_len = anzahl_relations
                                    
                                current_tabs = driver.window_handles
                                
                                for j in range(anzahl_relations):
                                    
                                    
                                    driver.switch_to.window(driver.window_handles[total_len + j])
                                    akt_relations.append(total_len + j)
                                    geclaimt = False
                                    
                                    XPATH = "/html/body/div[2]/form/table[2]/tbody/tr/td[3]/div/span/span/a"
                                    era_status = driver.find_element(By.XPATH, XPATH)
                                    era_status.click()
                                    
                                    try: 
                                        
                                        XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[2]/input"
                                        claim_button = driver.find_element(By.XPATH, XPATH)
                                        
                                    except:
                                        
                                        geclaimt = True
                                        XPATH = "/html/body/div[2]/form/table[1]/tbody/tr/th"
                                        title = driver.find_element(By.XPATH, XPATH)
                                        mother_name = title.text.lstrip("Firma ")
                                        
                                        XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table/tbody/tr/td[1]/div[1]"
                                        status = driver.find_element(By.XPATH, XPATH)

                                        XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table/tbody/tr/td[2]/div[1]"
                                        partner = driver.find_element(By.XPATH, XPATH)

                                        XPATH = "/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table/tbody/tr/td[3]/div[1]"
                                        tage = driver.find_element(By.XPATH, XPATH)
                                        
                                        if status.text != "Client":
                                            
                                            tage = int(''.join(filter(str.isdigit, tage.text)))
                                            tage = datetime.today() - timedelta(days=tage)
                                            tage = tage.replace(hour=0, minute=0, second=0, microsecond=0)
                                            
                                        else:
                                            
                                            tage = datetime.strptime(tage.text, '%Y-%m-%d')
                                        
                                        mothers = pd.concat([mothers, pd.DataFrame([[mother_name, total_len + j, True, name, partner.text, tage, status.text]], columns=columns_m)], ignore_index=True)    
                                        
                                        clicker("/html/body/div[2]/form/table[2]/tbody/tr/td[1]/span/span/a")
                                        
                                    if geclaimt == False:
                                        
                                        clicker("/html/body/div[2]/form/table[2]/tbody/tr/td[1]/span/span/a")
                                        
                                        XPATH = "/html/body/div[2]/form/table[1]/tbody/tr/th"
                                        title = driver.find_element(By.XPATH, XPATH)
                                        mother_name = title.text.lstrip("Firma ")
                                        
                                        mothers = pd.concat([mothers, pd.DataFrame([[mother_name, total_len + j, False, name]], columns=columns_miss)], ignore_index=True)    

                                    
                                total_len += add_to_len
                                    
                                driver.switch_to.window(driver.window_handles[i-adjust])
                    
                    else:
                        
                        print("Dupicate or no DUNS-number")
                        
                        driver.close()
                        adjust += 1
                        total_len = total_len - 1
                
                if self.check_before_claim:
                    self.progressUpdated.emit(30 + int((i / start_len) * 50))           
                else:
                    self.progressUpdated.emit(30 + int((i / start_len) * 40))
            
            if self.check_before_claim:        
                self.progressUpdated.emit(80)
            else:
                self.progressUpdated.emit(70)
            
            mothers, daughters, repeat, new_start, total_len, adjust = mother_search(start_len, total_len, daughters, mothers, adjust)
            
            if self.check_before_claim:
                self.progressUpdated.emit(85)
            else:
                self.progressUpdated.emit(75)
            while repeat == True:
                
                mothers, daughters, repeat, new_start, total_len, adjust = mother_search(new_start, total_len, daughters, mothers, adjust)
            
            if self.check_before_claim:
                self.progressUpdated.emit(90)
            else:
                self.progressUpdated.emit(80)
                
            grandclaim = []
            tables = {}

            start_tabs = daughters[:start_len-1] 

            for firma in start_tabs["Firma"]:
                
                akt = pd.DataFrame()
                zeiger = firma
                claim = False
                
                for index, row in mothers.iterrows():
                    
                    if row["Tochter"] == zeiger:
                                        
                        # get same result from line above but use concat instead of append
                        
                        akt = pd.concat([akt, pd.DataFrame([[row["Firma"], row["Tab"], row["Geclaimt"], row["Tochter"], row["Geclaimt/Client von"], row["Geclaimt/Client seit"], row["Status"]]], columns=columns_m)], ignore_index=True)
                        
                        zeiger = row["Firma"]
                        
                        if row["Geclaimt"] == True:
                            
                            claim = True
                            
                if (not akt.empty) and claim:
                    
                    grandclaim.append(akt.iloc[0, 3])
                        
                    tables[firma] = akt
                    
            daughters_with_claimed_mothers = start_tabs[start_tabs["Firma"].isin(grandclaim)]
            
            keep_open = start_tabs[~start_tabs["Firma"].isin(daughters_with_claimed_mothers["Firma"])]
            print(keep_open)
            
            # Erstelle ein DataFrame mit den Namen der Firmen aus der Spalte "Firma" in einer Spalte "Prospects" und füge für jede Firma den Wert von self.branche in die Spalte "Branche" ein
            prospects_with_branche = pd.DataFrame()
            prospects_with_branche["Prospects"] = keep_open["Firma"]
            prospects_with_branche["Branche"] = self.branche
            self.sendProspectsWithBranche.emit(prospects_with_branche)
            
            keep_open = keep_open["Tab"].tolist()
            
            start = len(keep_open) + 1
            add = (len(driver.window_handles)-1) - len(daughters)
            end = start + add

            adjust = 0

            for index, row in daughters.iterrows():
                
                driver.switch_to.window(driver.window_handles[row["Tab"]-adjust])
                
                if not row["Tab"] in keep_open:
                    
                    adjust += 1
                    driver.close()
                    
            adjust = 0

            for i in range(start, end):
                
                driver.switch_to.window(driver.window_handles[i-adjust])
                driver.close()
                adjust += 1
                    
            claimLog = pd.DataFrame()

            for index, row in daughters_with_claimed_mothers.iterrows():
                
                # get same result from line above but use concat instead of append
                
                claimLog = pd.concat([claimLog, pd.DataFrame([[row["Firma"]]], columns=["Firma"])], ignore_index=True)
                
                df = tables[row["Firma"]]
                claimLog = pd.concat([claimLog, df], ignore_index=True)
                
            try:
            
                claimLog.drop(columns={"Tab", "Geclaimt"}, inplace=True)
            
            except:
                
                print("Keine geclaimten Mütter")
            
            self.sendClaimedDf.emit(claimLog)
                    
            tabs = driver.window_handles
            
            counter = 1        
            for i in tabs:

                driver.switch_to.window(i)

                if i != driver.window_handles[0]:
                    
                    if self.last_claimed != "---":
                        
                        clicker("/html/body/div[2]/form/table[2]/tbody/tr/td[7]/div/span/span/a")
                        clicker("/html/body/div[2]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td/span/input")
                        
                        try:
                            
                            clicker("/html/body/div[2]/form/table[3]/tbody/tr/td/table[2]/tbody/tr[2]/td[3]/a")
                                
                        except:
                            
                            print("Kein Vorgang")
                            
                    if self.check_before_claim:
                        self.progressUpdated.emit(90 + int((counter / (len(tabs)-1)) * 10))
                    else:
                        self.progressUpdated.emit(80 + int((counter / (len(tabs)-1)) * 10))
                                    
            self.anzahl_prospects = anzahl_prospects - len(daughters_with_claimed_mothers)
            self.prospects_geclaimt = self.anzahl_prospects
            print(f"Es wurden {self.anzahl_prospects} valide Prospects gefunden")
            
            # Check if the radio button "Vor dem Claim überprüfen" is checked
            if self.check_before_claim:
                
                self.progressUpdated.emit(100)
                self.finished.emit(self.anzahl_prospects)
            
            else:
                
                print("Alle Prospects wurden geclaimt...")
                    
                ## Hier werden nun die gefundenen Prospects geclaimed und deren Vorgänge gepflegt

                tabs = driver.window_handles
                counter = 1

                for i in tabs:
                    driver.switch_to.window(i)

                    if i != driver.window_handles[0]:

                        clicker("//*[@id=\"main_container\"]/form/table[2]/tbody/tr/td[3]/div/span/span/a")
                        clicker("//*[@id=\"main_container\"]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[2]/input")
                        clicker("//*[@id=\"main_container\"]/form/table[2]/tbody/tr/td[7]/div/span/span/a")
                        clicker("//*[@id=\"main_container\"]/form/table[3]/tbody/tr/td/table[2]/tbody/tr[2]/td[3]/a")
                        clicker("/html/body/form/table[4]/tbody/tr[1]/td[2]/input")
                        
                        XPATH = "/html/body/form/table[2]/tbody/tr[1]/td[2]/textarea"
                        text = driver.find_element(By.XPATH, XPATH)
                        text.send_keys(self.aktion)
                        
                        clicker("//*[@id=\"holdfile_vs_appointment_empty\"]")
                        clicker("/html/body/form/table[2]/tbody/tr[10]/td[2]/input[1]")
                        clicker("/html/body/form/div[2]/p/table/tbody/tr/td[2]/a[1]/i")
                        
                        if self.ids.status.text == "A - Prospect/AP qualifiziert":
                            clicker("/html/body/form/table[2]/tbody/tr[7]/td[2]/select[1]/option[1]")
                            
                        if self.ids.status.text == "B - An Telemarketing übergeben":
                            clicker("/html/body/form/table[2]/tbody/tr[7]/td[2]/select[1]/option[2]")  
                            
                        clicker("/html/body/form/table[2]/tbody/tr[8]/td[2]/input[1]")
                        
                    self.progressUpdated.emit(90 + int((counter / self.anzahl_prospects) * 10))
                    counter = counter + 1

                self.finished.emit()
                return anzahl_prospects
        
    class AutomationThread_W(QThread):
        progressUpdated = pyqtSignal(int)
        finished = pyqtSignal(int)
        
        def __init__(self, last_claimed, action_text, status_text):
            QThread.__init__(self)
            self.last_claimed = last_claimed
            self.action_text = action_text
            self.status_text = status_text
            
        def run(self):
            print("Continuation Thread started")
            driver.switch_to.window(driver.window_handles[0])
            self.anzahl_prospects = len(driver.window_handles) - 1
            
            ### Hier werden nun die gefundenen Prospects geclaimed und deren Vorgänge gepflegt

            tabs = driver.window_handles
            
            if len(tabs) == 1:
                
                self.finished.emit(0)
                return

            
            counter = 1
            
            for i in tabs:
                driver.switch_to.window(i)

                if i != driver.window_handles[0]:
                    
                    if self.last_claimed != "---":
                        
                        ### Hier wird eine Exception für geclaimte Prospects ohne Vorgang gemacht
                        
                        try:
                    
                            clicker("/html/body/form/table[1]/tbody/tr/th/a")
                            
                        except:
                            
                            print("Kein Vorgang")
                        
                    clicker("//*[@id=\"main_container\"]/form/table[2]/tbody/tr/td[3]/div/span/span/a")
                    clicker("//*[@id=\"main_container\"]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[2]/input")
                    clicker("//*[@id=\"main_container\"]/form/table[2]/tbody/tr/td[7]/div/span/span/a")
                    clicker("//*[@id=\"main_container\"]/form/table[3]/tbody/tr/td/table[2]/tbody/tr[2]/td[3]/a")
                    clicker("/html/body/form/table[4]/tbody/tr[1]/td[2]/input")
                    
                    XPATH = "/html/body/form/table[2]/tbody/tr[1]/td[2]/textarea"
                    text = driver.find_element(By.XPATH, XPATH)
                    text.send_keys(self.action_text)
                    
                    clicker("//*[@id=\"holdfile_vs_appointment_empty\"]")
                    clicker("/html/body/form/table[2]/tbody/tr[10]/td[2]/input[1]")
                    clicker("/html/body/form/div[2]/p/table/tbody/tr/td[2]/a[1]/i")
                    
                    if self.status_text == "A - Prospect/AP qualifiziert":
                        clicker("/html/body/form/table[2]/tbody/tr[7]/td[2]/select[1]/option[1]")
                        
                    if self.status_text == "B - An Telemarketing übergeben":
                        clicker("/html/body/form/table[2]/tbody/tr[7]/td[2]/select[1]/option[2]")  
                        
                    clicker("/html/body/form/table[2]/tbody/tr[8]/td[2]/input[1]")
                    
                self.progressUpdated.emit(int((counter/self.anzahl_prospects) * 100))
                counter = counter + 1
                
            self.finished.emit(self.anzahl_prospects)
    
    def on_back(self):
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
        self.title = QLabel('Es wurden 20 neue Prospects geclaimt!')
        self.title.setObjectName('title')
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setMinimumHeight(100)
        titleLayout.addWidget(self.title)
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
        middleTitle = QLabel('Hier kannst Du nun die Ansprechpartner deiner soeben geclaimten Prospects exportieren:')
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
        
        tabs = driver.window_handles

        for i in tabs:

            driver.switch_to.window(i)

            if i != driver.window_handles[0]:
                
                driver.close()
        
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        self.parent().setCurrentIndex(2)
        
    def export(self):
        
        tabs = driver.window_handles

        for i in tabs:

            driver.switch_to.window(i)

            if i != driver.window_handles[0]:
                
                driver.close()
        
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        search_address = driver.find_element(By.ID, "button_plugins")
        search_address.click()

        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_main")
        XPATH = "/html/body/div[1]"
        search_search = driver.find_element(By.XPATH, XPATH)
        search_search.click()
        
        clicker("/html/body/form/table[3]/tbody/tr/td/a[2]")
        clicker("/html/body/form/table[2]/tbody/tr[1]/td[2]/input[1]")
        clicker("/html/body/form/table[2]/tbody/tr[2]/td[2]/input")
        clicker("/html/body/form/table[2]/tbody/tr[3]/td[2]/input")
        clicker("/html/body/form/center/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr[2]/td/input[4]")
        clicker("/html/body/form/center/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr[3]/td/button")

        self.parent().setCurrentIndex(5)
        
    def back(self):
        
        tabs = driver.window_handles

        for i in tabs:

            driver.switch_to.window(i)

            if i != driver.window_handles[0]:
                
                driver.close()
                
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        clicker("/html/body/form/div/ul/li[1]")
        
        self.parent().setCurrentIndex(1) 

# Export Screen
class ExportScreen(QWidget):
    
    sendFilePath = pyqtSignal(str)
    sendAPAge = pyqtSignal(str)
    
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
        
        # Öffne Datei Button und Textfeld
        
        self.pathLayout = QVBoxLayout()
        self.fileNameLine = QLineEdit()
        self.fileNameLine.setPlaceholderText('Datei auswählen oder Pfad eingeben')
        self.fileButton = QPushButton('Datei öffnen')
        # self.fileButton.setMaximumWidth(int(self.width() - 25))
        # self.fileButton.setMinimumWidth(int(self.width() - 25))
        self.applyShadow(self.fileButton)
        self.fileButton.clicked.connect(self.openFileDialog)
        self.pathLayout.addWidget(self.fileNameLine)
        self.pathLayout.addWidget(self.fileButton)
        self.pathLayout.setSpacing(5)
        self.pathLayout.setAlignment(Qt.AlignCenter)
        self.formLayout.addLayout(self.pathLayout)
        
        # "Geclaimt vor"-Dropdown
        
        claimedLayout = QHBoxLayout()
        claimedLabel = QLabel('Geclaimt vor:')
        self.claimedDropdown = QComboBox()
        self.claimedDropdown.addItems(["Heute", "1 Woche", "1 Monat", "3 Monaten", "6 Monaten", "1 Jahr"])
        self.applyShadow(self.claimedDropdown)
        claimedLayout.addWidget(claimedLabel)
        claimedLayout.addWidget(self.claimedDropdown)
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
        mainLayout.setSpacing(100)

    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
    
    # def sendFilePath(self, path):
    #     self.sendFilePath.emit(path)
    
    def openFileDialog(self):
        print("Datei öffnen")
        options = QFileDialog.Options()
        self.fileName, _ = QFileDialog.getOpenFileName(self, "Datei öffnen", "",
                                                  "Alle Dateien (*);;Textdateien (*.txt)", options=options)
        if self.fileName:
            print(self.fileName)
            self.sendFilePath.emit(self.fileName)
        
        # Disable the button after the file has been selected
        self.nextButton.setEnabled(True)
        self.nextButton.setStyleSheet("background-color: #387ADF; color: white;")
        # Reactivate the buttons hover effect
        self.nextButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        self.fileNameLine.setText(self.fileName)
        
    def export(self):
        print("Ansprechpartner exportieren")
        self.sendAPAge.emit(self.claimedDropdown.currentText())
        self.parent().setCurrentIndex(6)
        
    def back(self):
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        clicker("/html/body/form/div/ul/li[1]")
        self.parent().setCurrentIndex(1)

# AP Screen
class ApScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        #Erstelle ein DataFrame, mit den Spalten "Prospects" und "Branche"
        self.branchen = pd.DataFrame(columns=["Prospects", "Branche"])
        self.claimedDfExport = pd.DataFrame()
        
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
            QTableWidget::item:selected {
                background-color: #387ADF;
                color: #FFFFFF;
            }
        """)
        
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        titleLayout = QVBoxLayout()
        self.title = QLabel('Wähle nun aus welche der unten aufgeführten Funktionen die APS im Unternehmen haben dürfen! Wähle anschließend einen Speicherort aus, damit PAT Deine neuen Ansprechpartner berechnen kann und diese dort abspeichern kann:')
        self.title.setWordWrap(True)
        self.title.setObjectName('title')
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setMinimumHeight(100)
        titleLayout.addWidget(self.title)
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
        # Textfeld für den Speicherort, welches den ausgewählten Speicherort anzeigt und das Bearbeiten und einfügen ermöglicht
        self.folderNameLabel = QLineEdit()
        self.folderNameLabel.setPlaceholderText('Speicherort auswählen oder Pfad einfügen')
        saveButton.setMinimumHeight(55)
        self.exportButton.setMinimumHeight(55)
        self.applyShadow(saveButton)
        self.applyShadow(self.exportButton)
        buttonsLayout.addWidget(saveButton)
        buttonsLayout.addWidget(self.exportButton)
        buttonsLayout.setSpacing(5)
        pathLayout = QVBoxLayout()
        pathLayout.addWidget(self.folderNameLabel)
        pathLayout.addLayout(buttonsLayout)
        pathLayout.setAlignment(Qt.AlignCenter)
        pathLayout.setSpacing(5)
        mainLayout.addLayout(pathLayout)
        
        # Ein Button um den Vorgang abzubrechen und zurück zu gehen
        
        self.backButton = QPushButton('Zurück')
        self.applyShadow(self.backButton)
        mainLayout.addWidget(self.backButton)
        self.backButton.clicked.connect(self.back)
        
        mainLayout.setSpacing(75)
        self.resizeTable()

    def on_enter(self):
        
        self.backButton.setText('Zurück')
        
        self.exportDf = pd.read_excel(self.filePath, index_col=False)
        import_date = dt.datetime.today()
        
        print(self.age)
        
        if self.age == "Heute":
            import_date = import_date + dt.timedelta(days=360-1)
        
        if self.age == "1 Woche":
            import_date = import_date + dt.timedelta(days=360-8)
            
        elif self.age == "1 Monat":
            import_date = import_date + dt.timedelta(days=360-31)
            
        elif self.age == "3 Monaten":
            import_date = import_date + dt.timedelta(days=360-91) 
            
        elif self.age == "6 Monaten":
            import_date = import_date + dt.timedelta(days=360-121) 
            
        elif self.age == "1 Jahr":
            import_date = import_date + dt.timedelta(days=360-361)
            
        self.exportDf["Claim-Ende"] = pd.to_datetime(self.exportDf["Claim-Ende"], format="%d.%m.%Y", dayfirst=False)
        self.exportDf = self.exportDf[self.exportDf["Claim-Ende"] >= import_date]

        choose_function = []

        cF = self.exportDf[self.exportDf["Funktion"].notna()]

        for funk in cF["Funktion"]:
            
            for f in str(funk).split(","):
                
                f = f.lstrip()
                f = f.rstrip()
                
                if not f in choose_function:
                    
                    choose_function.append(f)     
                    
        self.cF = pd.DataFrame(choose_function, columns=["Funktion"])
        self.cF.sort_values(by="Funktion", inplace=True)
        
        # Setzen der Tabelle Dimension
        self.tableWidget.setRowCount(self.cF.shape[0])
        self.tableWidget.setColumnCount(self.cF.shape[1])

        # Füllen des QTableWidget mit Daten aus dem DataFrame
        for i in range(self.cF.shape[0]):
            for j in range(self.cF.shape[1]):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(self.cF.iloc[i, j])))

        # Setzen der Spaltenüberschriften
        self.tableWidget.setHorizontalHeaderLabels(self.cF.columns)
        # Erlauben der Zeilenauswahl
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        # Erlauben der Auswahl von mehreren Zeilen
        self.tableWidget.setSelectionMode(QTableWidget.MultiSelection)
        
    def receiveFilePath(self, filePath):
        # Verarbeiten Sie den empfangenen Dateipfad
        print(f"Empfangener Dateipfad: {filePath}")
        self.filePath = filePath
        
    def receiveAPAge(self, age):
        # Verarbeiten Sie das empfangene Alter
        print(f"Empfangenes Alter: {age}")
        self.age = age
        
    def receiveBranche(self, branche):
        # Verarbeiten Sie die empfangene Branche
        print(f"Empfangene Branche: {branche}")
        self.branche = branche
        
    def receiveClaimedDf(self, claimedDf):
        # Verarbeiten Sie das empfangene DataFrame
        print(f"Empfangenes DataFrame: {claimedDf}")
        self.claimedDf = claimedDf
        
        # Hinzufügen des DataFrames in das vollständig leere DataFrame "claimedDfExport"
        self.claimedDfExport = pd.concat([self.claimedDfExport, self.claimedDf], ignore_index=True)
    
    def receiveProspectsWithBranche(self, prospectsWithBranche):
        # Verarbeiten Sie die empfangenen Prospects
        print(f"Empfangene Prospects: {prospectsWithBranche}")
        self.prospectsWithBranche = prospectsWithBranche
        
        #Füge die empfangenen Prospects in das DataFrame "branchen" ein ohne die Methode append zu verwenden
        self.branchen = pd.concat([self.branchen, self.prospectsWithBranche], ignore_index=True)
              
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
            self.folderName = folderName
        
        # Aktivieren des "Berechnen"-Buttons
        self.exportButton.setEnabled(True)
        self.exportButton.setStyleSheet("background-color: #387ADF; color: white;")
        self.exportButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        self.folderNameLabel.setText(self.folderName)
    
    def export(self):
        print("---------------------------------------------------------")
        print("Speicherort = " + self.folderName)
        print("---------------------------------------------------------")
        
        ### Einlesen des neuen datas
        export = self.exportDf
        template = pd.DataFrame(columns = ['Organisation (Unternehmen)', 'Straße', 'PLZ', 'Ort', 'Anrede', 'Vorname', 'Nachname', 'Position', 'Telefon Zentrale', 'Telefon direkt 1', 'Telefon direkt 2', 'Pers. E-Mail', 'E-Mail Unternehmen', 'Webseite Unternehmen', 'Duns-Nummer', 'Industrie', 'Ihre ID', 'Notizen', 'Datum eingeliefert', 'CVR Media Import'])
        data = pd.DataFrame()
        funktionen = [item.text() for item in self.tableWidget.selectedItems()]
        
        
        firmen = export["Firmenname"].unique()
        options = funktionen

        for firma in firmen:
            
            akt = export[export["Firmenname"] == firma]
            
            if len(akt)<=1:
                
                data = pd.concat([data, akt])
                    
            else:
                
                ceo = akt[akt["Leitungsebene"]=="Top-Management"]
                ceo = ceo[ceo["Visitenkarten-Info"].str.contains("Geschäfts", na=False)]
                ceo.sort_values(by="Visitenkarten-Info", ascending=True, inplace=True)
                
                if len(ceo) >= 3:
                    
                    for index, row in ceo.iterrows():
                        
                        funk = str(row["Funktion"])
                        
                        if not funk == "nan":
                            
                            print(funk)
                            trigger = any(x in funk for x in options)
                            
                            if not trigger:
                                
                                ceo.drop(labels=index, axis=0)
                        
                    data = pd.concat([data, ceo.head(3)])
                                    
                elif len(ceo) > 0 and len(ceo) < 3:
                    
                    data = pd.concat([data, ceo])
                    miss = len(ceo)
                    
                    other = akt[akt["Funktion"].notna()]
                    other = other[other["Funktion"].str.contains('|'.join(options), na=False)]
                    
                    data = pd.concat([data, other.head(3-miss)])
                    
                elif len(ceo) == 0:
                    
                    other = akt[akt["Funktion"].notna()]
                    other = other[other["Funktion"].str.contains('|'.join(options), na=False)]
                    
                    if len(other)>0:
                        
                        data = pd.concat([data, other.head(3)])
                        
                    else:
                        
                        data = pd.concat([data, akt.head(1)])
                        print("Hit")

        data.drop(data[data["Telefon"].isna()].index, inplace=True)
        data.reset_index(inplace=True, drop=True)

        template["Organisation (Unternehmen)"] = data["Firmenname"]
        template["Straße"] = data["Straße"]+" "+data["Hausnummer"]
        template["PLZ"] = data["PLZ"]
        template["Ort"] = data["Ort"]
        template["Anrede"] = data["Serienbriefanrede"].str.split(" ").str[2]
        template["Vorname"] = data["Vorname"]
        template["Nachname"] = data["Name"]

        for index, row in data.iterrows():
            
            if row["Visitenkarten-Info"] == "Geschäftsführer":
                template.iloc[index, 7]= row["Visitenkarten-Info"]
                
            else:
                
                info = str(row["Visitenkarten-Info"])
                funk = str(row["Funktion"])
                
                if funk!="nan":
                    template.iloc[index, 7]= info + " " + funk
                else:
                    template.iloc[index, 7]= info
            
            St = str(row["Straße"])
            hN = str(row["Hausnummer"])
            
            if hN != "nan":
                template.iloc[index, 1] = St+" "+hN
            
            else:
                template.iloc[index, 1] = St
                
        template["Telefon Zentrale"] = data["Telefon"]
        template["Pers. E-Mail"] = data["AP-Email"]
        template["E-Mail Unternehmen"] = data["Email"]
        template["Webseite Unternehmen"] = data["Webseite"]
        template["Duns-Nummer"] = data["DUNS-Nummer"]
        for index, row in template.iterrows():
            for index2, row2 in self.branchen.iterrows():
                if row["Organisation (Unternehmen)"] == row2["Prospects"]:
                    template.at[index, "Industrie"] = row2["Branche"]
                    
        template["Datum eingeliefert"] = dt.datetime.today()

        export_date = dt.datetime.today()
        export_date = export_date.strftime("%d_%m_%Y")

        template.to_excel(f"{self.folderName}/CVR_Import_APs_{export_date}.xlsx", index=False)

        self.claimedDfExport.to_excel(f"{self.folderName}/Claimed_Prospects_Protokoll_{export_date}.xlsx", index=False)
        
        # Benachrichtigung, dass der Export abgeschlossen und die Datei gespeichert wurde. Dabei soll das Label zusätzlich noch den Pfad zur Datei anzeigen. Es soll rot markiert sein, damit es auffällt.
        self.title.setText(f'Der Export wurde erfolgreich abgeschlossen! Die Datei wurde unter folgendem Pfad gespeichert: {self.folderName}/CVR_Import_APs_{export_date}.xlsx')
        self.title.setStyleSheet("background-color: #990000")
        
        #Der Benutzer kann nun nicht mehr auf den "Export"-Button klicken und dieser wird grau dargestellt.
        self.exportButton.setEnabled(False)
        self.exportButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        self.backButton.setText('Abschließen')
        
    def back(self):
        print("Zurück geklickt")
        
        tabs = driver.window_handles

        for i in tabs:

            driver.switch_to.window(i)

            if i != driver.window_handles[0]:
                
                driver.close()
                
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        self.parent().setCurrentIndex(1)
        
# Unclaim Screen
class UnclaimScreen(QWidget):
    def __init__(self, changeScreenCallback, startAutomationCallback):
        self.changeScreenCallback = changeScreenCallback
        self.startAutomationCallback = startAutomationCallback
        self.beenVisited = False
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
        self.title = QLabel('Im Folgenden wird dein Dashboard analysiert, um Prospects zu finden die entclaimt werden sollen:')
        self.title.setObjectName('title')
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignCenter)
        # title.setMaximumHeight(100)
        titleLayout.addWidget(self.title)
        mainLayout.addLayout(titleLayout)
        
        # Es soll gewählt werden können, ob die Prospects vor dem Unclaimen noch überprüft werden sollen
        
        radioLayout = QHBoxLayout()
        checkBeforeUnclaimLabel = QLabel('Vor dem Unclaimen überprüfen')
        self.checkBeforeUnclaim = QRadioButton()
        # make the radio button bigger so that it is easier to click
        self.checkBeforeUnclaim.setMinimumHeight(200)
        self.checkBeforeUnclaim.setMinimumHeight(75)
        # checkBeforeUnclaim.setChecked(True)
        radioLayout.addWidget(checkBeforeUnclaimLabel)
        radioLayout.addWidget(self.checkBeforeUnclaim)
        radioLayout.setSpacing(25)
        mainLayout.addLayout(radioLayout)
        
        # 3 Buttons in einer Horizontalen Box: "Unclaimen", "Weiter" und "Abbrechen". Der "Weiter"-Button soll erst aktiviert werden, wenn der "Unclaimen"-Button geklickt wurde und der Radio-Button auf "Vor dem Unclaimen überprüfen" gesetzt wurde.
        
        buttonsLayout = QHBoxLayout()
        self.unclaimButton = QPushButton('Unclaimen')
        self.unclaimButton .clicked.connect(self.on_unclaim)
        self.nextButton = QPushButton('Weiter')
        self.nextButton.setEnabled(False)
        self.nextButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        self.nextButton.clicked.connect(self.on_weiter)
        self.cancelButton = QPushButton('Abbrechen')
        self.cancelButton.clicked.connect(self.on_cancel)
        self.applyShadow(self.unclaimButton )
        self.applyShadow(self.nextButton)
        self.applyShadow(self.cancelButton)
        buttonsLayout.addWidget(self.unclaimButton )
        buttonsLayout.addWidget(self.nextButton)
        buttonsLayout.addWidget(self.cancelButton)
        buttonsLayout.setSpacing(5)
        mainLayout.addLayout(buttonsLayout)
        
        mainLayout.setSpacing(200)
        mainLayout.setAlignment(radioLayout, Qt.AlignCenter)
    
    def on_enter(self):
        
        if self.beenVisited:
            # Reset the title label and the buttons
            self.title.setText('Im Folgenden wird dein Dashboard analysiert, um Prospects zu finden die entclaimt werden sollen:')
            self.title.setStyleSheet("background-color: #387ADF")
            self.unclaimButton.setEnabled(True)
            self.unclaimButton.setStyleSheet("background-color: #387ADF; color: white;")
            self.unclaimButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
            self.nextButton.setEnabled(False)
            self.nextButton.setStyleSheet("background-color: #AAAAAA; color: white;")
            self.beenVisited = False
    
    class AutomationThread_U(QThread):
        progressUpdated = pyqtSignal(int)
        finished = pyqtSignal(int)
        
        def __init__(self, with_check):
            super().__init__()
            self.with_check = with_check
            
        def run(self):
            # Automatisieren Sie den Unclaim-Prozess hier
            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.frame("frame_main")
            XPATH = "//*[@id=\"body_div\"]/form/table/tbody/tr[2]/td[1]/table[3]/tbody/tr[2]/td/table[2]"
            table_WV = driver.find_element(By.XPATH, XPATH)
            wvs = table_WV.find_elements(By.TAG_NAME, "tr")
            
            XPATH = "/html/body/div[2]/form/table/tbody/tr[2]/td[1]/table[3]/tbody/tr[2]/td/table[1]/tbody/tr/td"
            seiten = driver.find_element(By.XPATH, XPATH)
            seiten = seiten.text
            seiten = seiten.split("von")[1]
            seiten = seiten.strip()
            seiten = int(seiten)
            
            self.progressUpdated.emit(5)
            
            if seiten > 1:
            
                for seite in range(seiten - 1):     ###
                    
                    XPATH = "//*[@id=\"body_div\"]/form/table/tbody/tr[2]/td[1]/table[3]/tbody/tr[2]/td/table[2]"
                    table_WV = driver.find_element(By.XPATH, XPATH)
                    wvs = table_WV.find_elements(By.TAG_NAME, "tr")

                    for texts in wvs:
                        text = texts.find_elements(By.TAG_NAME, "td")
                        for i in text:
                            if i.text.endswith("bitte unclaimen"):
                                l = i.find_element(By.TAG_NAME, "a")
                                l.send_keys(Keys.CONTROL + Keys.RETURN)
                    try:
                        XPATH = "//*[@id=\"body_div\"]/form/table/tbody/tr[2]/td[1]/table[3]/tbody/tr[2]/td/table[1]/tbody/tr/td/button"
                        nextPage = driver.find_element(By.XPATH, XPATH)
                        nextPage.click()
                        
                    except:
                        print("keine Seite mehr")
                        
                    self.progressUpdated.emit(5 + (seite/(seiten-1)) * 15)
                        
            else:
                counter = 1
                for texts in wvs:
                    text = texts.find_elements(By.TAG_NAME, "td")
                    for i in text:
                        if i.text.endswith("bitte unclaimen"):
                            l = i.find_element(By.TAG_NAME, "a")
                            l.send_keys(Keys.CONTROL + Keys.RETURN)
                    self.progressUpdated.emit(5 + counter/len(wvs) * 15)
                    counter += 1
                
            ## Hier Überprüfung
            if self.with_check:
                self.progressUpdated.emit(100)
                self.finished.emit(len(driver.window_handles)-1)
            
            else:
                
                tabs = driver.window_handles
                numberTabs = len(tabs)
                
                counter = 1
                for i in tabs:
                    driver.switch_to.window(i)
                    try:
                        clicker("/html/body/form/table[1]/tbody/tr/th/a")
                        self.progressUpdated.emit(20 + (counter/numberTabs) * 20)
                        print(counter/numberTabs * 20)
                        counter += 1
                    except:
                        print("first tab1")
                    
                counter = 1
                for i in tabs:
                    driver.switch_to.window(i)
                    try:
                        clicker("//*[@id=\"main_container\"]/form/table[2]/tbody/tr/td[3]/div/span/span/a")
                        self.progressUpdated.emit(40 + (counter/numberTabs) * 20)
                        counter += 1
                    except:
                        print("first tab2")
                    
                counter = 1    
                for i in tabs:
                    driver.switch_to.window(i)
                    try:
                        clicker("//*[@id=\"main_container\"]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[2]/input[1]")  
                        self.progressUpdated.emit(60 + (counter/numberTabs) * 20)
                        counter += 1
                    except:
                        print("first tab3")
                
                counter = 1    
                for i in tabs:
                    driver.switch_to.window(i)
                    try:
                        driver.switch_to.alert.accept()
                        self.progressUpdated.emit(80 + (counter/numberTabs) * 20)
                        counter += 1
                    except:
                        print("first tab4")
                    
                driver.switch_to.window(driver.window_handles[0])
                
                self.progressUpdated.emit(100)
                self.finished.emit(len(driver.window_handles)-1)
    
    class AutomationThread_W(QThread):
        progressUpdated = pyqtSignal(int)
        finished = pyqtSignal(int)
        
        def __init__(self):
            super().__init__()
            
        def run(self):
            driver.switch_to.window(driver.window_handles[0])
        
            tabs = driver.window_handles
            numberTabs = len(tabs)
            
            counter = 1
            for i in tabs:
                driver.switch_to.window(i)
                try:
                    clicker("/html/body/form/table[1]/tbody/tr/th/a")
                    self.progressUpdated.emit(counter/numberTabs * 40)
                    counter += 1
                except:
                    print("first tab1")
                
            counter = 1
            for i in tabs:
                driver.switch_to.window(i)
                try:
                    clicker("//*[@id=\"main_container\"]/form/table[2]/tbody/tr/td[3]/div/span/span/a") 
                    self.progressUpdated.emit(40 + counter/numberTabs * 30)
                    counter += 1
                except:
                    print("first tab2")
                
            counter = 1
            for i in tabs:
                driver.switch_to.window(i)
                try:
                    clicker("//*[@id=\"main_container\"]/form/table[3]/tbody/tr/td/table[1]/tbody/tr/td[2]/input[1]")  
                except:
                    print("first tab3")
                    
                try:
                    driver.switch_to.alert.accept()
                    self.progressUpdated.emit(70 + counter/numberTabs * 30)
                    counter += 1
                except:
                    print("first tab4")
            
            self.progressUpdated.emit(100)
            self.finished.emit(len(driver.window_handles)-1)    
        
    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(100)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        widget.setGraphicsEffect(shadow)
    
    def on_unclaim(self):
        self.startAutomationCallback()  # Startet die Automation
        self.changeScreenCallback(8)
        
    def on_weiter(self):
        self.startAutomationCallback()  # Startet die Automation
        self.changeScreenCallback(8)
    
    def on_cancel(self):
        self.beenVisited = True
        
        tabs = driver.window_handles

        for i in tabs:

            driver.switch_to.window(i)

            if i != driver.window_handles[0]:
                
                driver.close()
                
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.parent_frame()
        driver.switch_to.frame("frame_menu")
        clicker("/html/body/form/div/ul/li[1]")
        
        self.changeScreenCallback(1)

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
            QLabel, QProgressBar, QPushButton {
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
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateTimer)
        self.startTime = 0       
        
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
        # buttonsLayout.addWidget(self.nextButton)
        buttonsLayout.setSpacing(5)
        
        # Layout-Elemente hinzufügen
        main_layout.addLayout(titleLayout)
        main_layout.addLayout(middleLayout)
        main_layout.addLayout(buttonsLayout)
        main_layout.setAlignment(middleLayout, Qt.AlignCenter)
        main_layout.setSpacing(50)
        
    def startTimer(self):
        self.startTime = 0
        self.timer.start(1000)
        
    def updateTimer(self):
        self.startTime += 1
        self.timerLabel.setText(f"{self.startTime} Sekunden")
        
    # Setter Methoden für die Progress Bar und den "Weiter"-Button
    # Überprüfen!!!
    
    def setRange(self, value):
        self.progressBar.setRange(0, value)
        
    def setProgress(self, value):
        self.progressBar.setValue(value)
        
    def setLableProgressLabel(self, text):
        self.progressLabel.setText(text)
        
    def setNotificationLabel(self, text):
        self.notificationLabel.setText(text)
    
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
        
        # Signal verbinden
        self.stackedWidget.currentChanged.connect(self.on_screen_changed)

        self.loginScreen = LoginScreen()
        self.chooseScreen = ChooseScreen(self.setCurrentIndex, self.chooseScreenAutomation)
        self.searchScreen = SearchScreen()
        self.claimScreen = ClaimScreen(self.setCurrentIndex, self.claimScreenAutomation)
        self.finishScreen = FinishScreen()
        self.exportScreen = ExportScreen()
        self.apScreen = ApScreen()
        self.exportScreen.sendFilePath.connect(self.apScreen.receiveFilePath)
        self.exportScreen.sendAPAge.connect(self.apScreen.receiveAPAge)
        self.searchScreen.sendBranche.connect(self.apScreen.receiveBranche)
        self.unclaimScreen = UnclaimScreen(self.setCurrentIndex, self.unclaimScreenAutomation)
        self.loadingScreen = LoadingScreen()

        self.stackedWidget.addWidget(self.loginScreen)
        self.stackedWidget.addWidget(self.chooseScreen)
        self.stackedWidget.addWidget(self.searchScreen)
        self.stackedWidget.addWidget(self.claimScreen)
        self.stackedWidget.addWidget(self.finishScreen)
        self.stackedWidget.addWidget(self.exportScreen)
        self.stackedWidget.addWidget(self.apScreen)
        self.stackedWidget.addWidget(self.unclaimScreen)
        self.stackedWidget.addWidget(self.loadingScreen)
        
        ## Hier wird der automatische Login ausgeführt
        
        # Comment out the lines below to use manual login
        try:
            
            kr_user = keyring.get_password(service_id_user, MAGIC_USERNAME_KEY)
            kr_pw = keyring.get_password(service_id_pass, MAGIC_USERNAME_KEY)
                        
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
                    search_mandant.clear()
                    search_email.clear()
                    search_passwort.clear()
                    
        except:
            print("Kein Passwort gefunden!")
        
    def setCurrentIndex(self, index):
        self.stackedWidget.setCurrentIndex(index)
    
    ### Methoden für den Choose Screen ###
        
    # Methode für den Thread von des Choose Screens
    def chooseScreenAutomation(self):
        self.automationThread = self.chooseScreen.AutomationThread()
        self.automationThread.progressUpdated.connect(self.updateProgress)
        self.automationThread.finished.connect(self.onAutomationComplete_choose)
        self.loadingScreen.setRange(100)
        self.loadingScreen.setLableProgressLabel("PAT lädt nun das Licensee-Plugin...")
        self.loadingScreen.setNotificationLabel("Dies kann einige Sekunden dauern...")
        self.loadingScreen.setProgress(0)
        self.setCurrentIndex(8)
        # Starte die Automation und wechsle zum Ladebildschirm
        self.automationThread.start()
        self.loadingScreen.startTimer()
    
    def onAutomationComplete_choose(self):
        self.stackedWidget.setCurrentWidget(self.searchScreen)

    ### Methoden für den Claim Screen ###
    def get_last_claimed(self):
        last_claimed_out = self.searchScreen.last_claimed
        return last_claimed_out
    
    def get_branche(self):
        branche_out = self.searchScreen.branche
        return branche_out
    
    def claimScreenAutomation(self):
        #Aufruf der Automation mit Übergabe der Parameter des Search Screens und Claim Screens
        self.automationThread = self.claimScreen.AutomationThread_S(self.get_last_claimed(), int(self.claimScreen.value_label.text()), self.claimScreen.check_before_claim.isChecked(), self.claimScreen.action_text.text(), self.get_branche())
        self.automationThread.progressUpdated.connect(self.updateProgress)
        self.automationThread.finished.connect(self.onAutomationComplete_claim)
        self.automationThread.sendClaimedDf.connect(self.apScreen.receiveClaimedDf)
        self.automationThread.sendProspectsWithBranche.connect(self.apScreen.receiveProspectsWithBranche)
        self.loadingScreen.setRange(100)
        self.loadingScreen.setLableProgressLabel("PAT analysiert nun die Prospects...")
        self.loadingScreen.setNotificationLabel("Dies kann einige Minuten dauern...")
        self.loadingScreen.setProgress(0)
        self.setCurrentIndex(8)
        # Starte die Automation und wechsle zum Ladebildschirm
        self.automationThread.start()
        self.loadingScreen.startTimer()
        
        if self.claimScreen.check_before_claim.isChecked():
            self.claimScreen.startAutomationCallback = self.claimScreenAutomation_weiter
            self.claimScreen.beenVisited = True
        
    def claimScreenAutomation_weiter(self):
        # Aufruf der Automation mit Übergabe der Parameter des Search Screens und Claim Screens
        self.automationThread = self.claimScreen.AutomationThread_W(self.get_last_claimed(), self.claimScreen.action_text.text(), self.claimScreen.status_dropdown.currentText())
        self.automationThread.progressUpdated.connect(self.updateProgress)
        self.automationThread.finished.connect(self.onAutomationComplete_claim_weiter)
        self.loadingScreen.setRange(100)
        self.loadingScreen.setLableProgressLabel("PAT claimt nun die Prospects...")
        self.loadingScreen.setNotificationLabel("Dies kann einige Minuten dauern...")
        self.loadingScreen.setProgress(0)
        self.setCurrentIndex(8)
        # Starte die Automation und wechsle zum Ladebildschirm
        self.automationThread.start()
        self.loadingScreen.startTimer()
    
    @pyqtSlot(int)    
    def onAutomationComplete_claim(self, result):
        
        if self.claimScreen.check_before_claim.isChecked():
            # Setze den Weiter-Button auf enabled und ändere die Hintergrundfarbe und die beiden anderen Buttons auf disabled und grau
            self.claimScreen.weiter_button.setEnabled(True)
            self.claimScreen.weiter_button.setStyleSheet("background-color: #387ADF; color: white;")
            self.claimScreen.weiter_button.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
            self.claimScreen.start_button.setEnabled(False)
            self.claimScreen.start_button.setStyleSheet("background-color: #AAAAAA; color: white;")
            self.claimScreen.back_button.setEnabled(False)
            self.claimScreen.back_button.setStyleSheet("background-color: #AAAAAA; color: white;")
        
            # Aktualisiere den Text des Title-Labels und färbe es rot
            self.claimScreen.title.setText(f"Es wurden {result} valide Prospects gefunden! Du kannst nun die Tabs der Prospects, die Du nicht claimen möchtest, schließen! Wenn Du anschließend auf \"Weiter\" klickst werden die verbleibenden Prospects geclaimt!")
            self.claimScreen.title.setStyleSheet("background-color: #990000;")
            
            self.stackedWidget.setCurrentWidget(self.claimScreen)
        else:
            self.stackedWidget.setCurrentWidget(self.finishScreen)    
    
    @pyqtSlot(int)    
    def onAutomationComplete_claim_weiter(self, result):
        self.stackedWidget.setCurrentWidget(self.finishScreen)
        self.finishScreen.title.setText(f"Es wurden {result} Prospects geclaimt!")
        self.claimScreen.beeinVisited = False
        self.automationThread.finished.connect(self.onAutomationComplete_claim)
        # Weise wieder die ursprüngliche Methode zu
        self.claimScreen.startAutomationCallback = self.claimScreenAutomation
    
    ### Methoden für den Unclaim Screen ###
    
    def unclaimScreenAutomation(self):
        self.automationThread = self.unclaimScreen.AutomationThread_U(self.unclaimScreen.checkBeforeUnclaim.isChecked())
        self.automationThread.progressUpdated.connect(self.updateProgress)
        if self.unclaimScreen.checkBeforeUnclaim.isChecked():
            self.automationThread.finished.connect(self.onAutomationComplete_unclaim_weiter)
            self.loadingScreen.setLableProgressLabel("PAT lädt nun die Vorgänge der Prospects...")
        else:
            self.automationThread.finished.connect(self.onAutomationComplete_unclaim)
            self.loadingScreen.setLableProgressLabel("PAT unclaimt nun die Prospects...")
        self.loadingScreen.setRange(100)
        self.loadingScreen.setNotificationLabel("Dies kann einige Minuten dauern...")
        self.loadingScreen.setProgress(0)
        self.setCurrentIndex(8)
        # Starte die Automation und wechsle zum Ladebildschirm
        self.automationThread.start()
        self.loadingScreen.startTimer()
        
        if self.unclaimScreen.checkBeforeUnclaim.isChecked():
            self.unclaimScreen.startAutomationCallback = self.unclaimScreenAutomation_weiter
    
    def unclaimScreenAutomation_weiter(self):
        self.automationThread = self.unclaimScreen.AutomationThread_U(self.unclaimScreen.checkBeforeUnclaim.isChecked())
        self.automationThread.progressUpdated.connect(self.updateProgress)
        self.automationThread.finished.connect(self.onAutomationComplete_unclaim)
        self.loadingScreen.setRange(100)
        self.loadingScreen.setLableProgressLabel("PAT unclaimt nun die Prospects...")
        self.loadingScreen.setNotificationLabel("Dies kann einige Minuten dauern...")
        self.loadingScreen.setProgress(0)
        self.setCurrentIndex(8)
        # Starte die Automation und wechsle zum Ladebildschirm
        self.automationThread.start()
        self.loadingScreen.startTimer()
        
        self.unclaimScreen.startAutomationCallback = self.unclaimScreenAutomation
    
    @pyqtSlot(int)
    def onAutomationComplete_unclaim(self, result):
        self.stackedWidget.setCurrentWidget(self.unclaimScreen)
        self.unclaimScreen.title.setText(f"Es wurden {result} Prospects unclaimt!")
        self.unclaimScreen.title.setStyleSheet("background-color: #990000;")
        self.unclaimScreen.unclaimButton.setEnabled(False)
        self.unclaimScreen.unclaimButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        # self.unclaimScreen.unclaimButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        self.unclaimScreen.nextButton.setEnabled(False)
        self.unclaimScreen.nextButton.setStyleSheet("background-color: #AAAAAA; color: white;")
        # self.unclaimScreen.nextButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        
    @pyqtSlot(int)
    def onAutomationComplete_unclaim_weiter(self, result):
        self.stackedWidget.setCurrentWidget(self.unclaimScreen)
        self.unclaimScreen.title.setText(f"Es wurden {result} Prospects gefunden, die unclaimt werden können! Du kannst nun die Tabs der Prospects, die Du nicht unclaimen möchtest, schließen! Wenn Du anschließend auf \"Weiter\" klickst werden die verbleibenden Prospects unclaimt!")
        self.unclaimScreen.title.setStyleSheet("background-color: #990000;")
        self.unclaimScreen.nextButton.setEnabled(True)
        self.unclaimScreen.nextButton.setStyleSheet("background-color: #387ADF; color: white;")
        self.unclaimScreen.nextButton.setStyleSheet("QPushButton:hover { background-color: #333A73; }")
        self.unclaimScreen.unclaimButton.setEnabled(False)
        self.unclaimScreen.unclaimButton.setStyleSheet("background-color: #AAAAAA; color: white;")
             
    ### Methoden für den Loading Screen ###
    def updateProgress(self, progress):
        self.loadingScreen.setProgress(progress)
        
    def on_screen_changed(self, index):
        # Zugriff auf das aktuelle Widget und Aufruf von on_enter
        screen = self.stackedWidget.currentWidget()
        if hasattr(screen, 'on_enter'):
            screen.on_enter()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())