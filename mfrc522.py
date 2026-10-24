import machine
import time

class MFRC522:
    def __init__(self, spi, cs, rst):
        self.spi = spi
        self.cs = cs
        self.rst = rst
        self.cs.value(1)
        self.rst.value(1)
        self.init()

    def _w(self, reg, val):
        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
        self.spi.write(b'%c' % int(0xff & val))
        self.cs.value(1)

    def _r(self, reg):
        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def sflags(self, reg, mask):
        self._w(reg, self._r(reg) | mask)

    def cflags(self, reg, mask):
        self._w(reg, self._r(reg) & (~mask))

    def tocard(self, cmd, send):
        recv = []
        bits = irq_en = wait_irq = n = 0import machine
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
        
    time.sleep(0.1)import machine
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
        stat = 2
        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30
        self._w(0x02, irq_en | 0x80)
        self.cflags(0x04, 0x80)
        self.sflags(0x0A, 0x80)
        self._w(0x01, 0x00)
        for c in send:
            self._w(0x09, c)
        self._w(0x01, cmd)
        if cmd == 0x0C:
            self.sflags(0x0D, 0x80)
        i = 2000
        while True:
            n = self._r(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break
        self.cflags(0x0D, 0x80)
        if i != 0:
            if (self._r(0x06) & 0x1B) == 0x00:
                stat = 0
                if n & irq_en & 0x01:
                    stat = 1
                elif cmd == 0x0C:
                    n = self._r(0x0A)
                    l = self._r(0x09) & 0x07
                    if l != 0:
                        bits = (n - 1) * 8 + l
                    else:
                        bits = n * 8
                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16
                    for _ in range(n):
                        recv.append(self._r(0x09))
            else:
                stat = 2
        return stat, recv, bits

    def request(self, req_mode):
        self._w(0x0D, 0x07)
        stat, recv, bits = self.tocard(0x0C, [req_mode])
        if (stat != 0) | (bits != 0x10):
            stat = 2
        return stat, bits

    def anticoll(self):
        ser_chk = 0
        ser = [0x93, 0x20]
        self._w(0x0D, 0x00)
        stat, recv, bits = self.tocard(0x0C, ser)
        if stat == 0:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = 2
            else:
                stat = 2
        return stat, recv

    def init(self):
        self.rst.value(0)
        time.sleep(0.05)
        self.rst.value(1)
        time.sleep(0.05)
        self._w(0x01, 0x0F)
        self._w(0x2A, 0x8D)
        self._w(0x2B, 0x3E)
        self._w(0x2D, 0x1E)
        self._w(0x2C, 0x00)
        self._w(0x15, 0x40)
        self._w(0x11, 0x3D)
        self.sflags(0x14, 0x03)

    def lese_chip(self):
        stat, _ = self.request(0x26)
        if stat == 0:
            stat, uid = self.anticoll()
            if stat == 0:
                return "-".join(["{:02X}".format(x) for x in uid])
        return None