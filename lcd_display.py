import time
import tm1637
import json

# Charger les définitions de pin depuis le fichier config.json
def load_pin_definitions(file_path):
    with open(file_path) as f:
        config = json.load(f)
        return config['lcd_pins']

pin_config = load_pin_definitions('config.json')

# Utiliser les définitions de pin chargées
CLK_E = pin_config['CLK_E']
DIO_E = pin_config['DIO_E']
CLK_S = pin_config['CLK_S']
DIO_S = pin_config['DIO_S']
CLK_A = pin_config['CLK_A']
DIO_A = pin_config['DIO_A']
CLK_H = pin_config['CLK_H']
DIO_H = pin_config['DIO_H']

# Initialize LCD displays
lcd_E = tm1637.TM1637("/dev/gpiochip0", clk=CLK_E, dio=DIO_E)
lcd_S = tm1637.TM1637("/dev/gpiochip0", clk=CLK_S, dio=DIO_S)
lcd_A = tm1637.TM1637("/dev/gpiochip0", clk=CLK_A, dio=DIO_A)
lcd_H = tm1637.TM1637("/dev/gpiochip0", clk=CLK_H, dio=DIO_H)

def display_temperature(display, temp):
    try:
        temp_str = "{:.1f}".format(temp)
        int_part, frac_part = temp_str.split(".")
        # Insérer un espace entre les deux premiers chiffres et le premier chiffre décimal
        display_str = f"{int_part[:2]} {frac_part[0]}"
        display.show(display_str)
    except (ValueError, TypeError) as e:
        print(f"Error displaying temperature on {display}: {e}")

def display_time(lcd):
    current_time = time.strftime("%H%M")
    lcd.show(current_time, colon=True)

def lcd_display_loop(temperatures):
    while True:
        display_temperature(lcd_E, temperatures['temp_E'])  # Température de l'eau de la piscine
        display_temperature(lcd_S, temperatures['temp_S'])  # Température de sortie du collecteur solaire
        display_temperature(lcd_A, temperatures['temp_A'])  # Température ambiante
        display_time(lcd_H)  # Afficher l'heure sur l'écran lcd_H
        time.sleep(1)
