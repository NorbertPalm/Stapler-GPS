import machine
import time
import framebuf
from mfrc522 import MFRC522

# --- 1. OLED Display einrichten ---
class OLED(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c):
        self.i2c = i2c
        self.addr = 0x3c 
        self.buffer = bytearray((height // 8) * width)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        for cmd in (0xAE, 0x20, 0x00, 0x40, 0xA1, 0xA8, 63, 0xC8, 0xD3, 0x00, 0xDA, 0x12, 0xD5, 0x80, 0xD9, 0x22, 0xDB, 0x30, 0x81, 0xFF, 0xA4, 0xA6, 0x8D, 0x14, 0xAF):
            self.i2c.writeto(self.addr, bytes([0x80, cmd]))
            
    def show(self):
        self.i2c.writeto(self.addr, b'\x40' + self.buffer)

# I2C Pins für das Display (SDA=Pin 0, SCL=Pin 1)
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
oled = OLED(128, 64, i2c)

# --- 2. Hardware-Setup RFID ---
# SPI Pins für den Scanner (SCK=Pin 6, MOSI=Pin 7, MISO=Pin 4)
# Die Baudrate ist hier für echte Hardware auf Standard (1.000.000) gesetzt.
spi = machine.SPI(0, baudrate=1000000, polarity=0, phase=0, sck=machine.Pin(6), mosi=machine.Pin(7), miso=machine.Pin(4))
cs = machine.Pin(5, machine.Pin.OUT)
rst = machine.Pin(8, machine.Pin.OUT)
rfid = MFRC522(spi, cs, rst)

# --- 3. CSV Daten einlesen ---
stationen = []
try:
    with open('stationen.csv', 'r') as datei:
        for zeile in datei:
            saubere_zeile = zeile.strip()
            if saubere_zeile != "":
                stationen.append(saubere_zeile)
except OSError:
    stationen = ["Halle 1 - Gang A", "Halle 1 - Gang B", "Halle 1 - Gang C", "Laderampe"]

aktuelle_position = 0 

def bildschirm_aktualisieren():
    oled.fill(0) 
    oled.text("Stapler-GPS", 20, 0)
    oled.text("----------------", 0, 10)
    oled.text("Aktuelle Pos:", 0, 30)
    oled.text(stationen[aktuelle_position], 0, 45)
    oled.show() 

bildschirm_aktualisieren()
print("Bordcomputer bereit. Warte auf erste Karte...")

# --- 4. Die echte Steuerung für die Halle ---
letzter_chip = ""

while True:
    # 0x26 ist der echte, physische Standard-Suchbefehl für RFID-Chips
    stat, _ = rfid.request(0x26) 
    
    if stat == 0:
        # Eine Karte ist in Reichweite! Wir lesen ihre einmalige Seriennummer (UID) aus.
        stat, uid = rfid.anticoll()
        if stat == 0:
            # Die Nummern werden in einen lesbaren Text verwandelt (z.B. "A1-B2-C3-D4")
            chip_id = "-".join(["{:02X}".format(x) for x in uid])
            
            # Die wichtigste Prüfung: Ist das ein NEUER Chip, den wir gerade überfahren?
            if chip_id != letzter_chip:
                print("TREFFER! Neue Karte überfahren. Seriennummer:", chip_id)
                letzter_chip = chip_id
                
                # Wir springen eine Station in der Liste weiter
                aktuelle_position = aktuelle_position + 1
                
                # Wenn wir am Ende der Liste sind, fangen wir wieder von vorne an
                if aktuelle_position >= len(stationen):
                    aktuelle_position = 0
                    
                bildschirm_aktualisieren()
                
                # Eine kurze Pause, damit das Display sauber aufbaut
                time.sleep(1)
                
    else:
        # Sobald der Stapler weiterfährt und KEIN Chip mehr in der Nähe ist, 
        # wird der Kurzzeit-Speicher geleert. So sind wir bereit für den nächsten Gang.
        letzter_chip = ""
        
    time.sleep(0.1)