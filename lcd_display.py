# lcd_display.py

import time
from TM1637 import TM1637

# Pin definitions
CLK_E = 13
DIO_E = 26
CLK_S = 27
DIO_S = 21
CLK_A = 19
DIO_A = 20
CLK_H = 23
DIO_H = 22

# Initialize LCD displays
lcd_E = TM1637(clk=CLK_E, dio=DIO_E)
lcd_S = TM1637(clk=CLK_S, dio=DIO_S)
lcd_A = TM1637(clk=CLK_A, dio=DIO_A)
lcd_H = TM1637(clk=CLK_H, dio=DIO_H)

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
    lcd.show(current_time)

def lcd_display_loop(temperatures):
    while True:
        display_temperature(lcd_E, temperatures['temp_E'])
        display_temperature(lcd_S, temperatures['temp_A'])
        display_temperature(lcd_A, temperatures['temp_S'])
        display_time(lcd_H)
        time.sleep(1)

if __name__ == "__main__":
    dummy_temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0}
    lcd_display_loop(dummy_temperatures)
