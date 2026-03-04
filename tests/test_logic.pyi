import sys
import os

# Додаємо шлях до папки src, щоб тест бачив ваш код
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(_file_), '..','src')))

from drone_monitor import DroneMonitor

def test_risk_assessment():
    monitor = 
DroneMonitor(safe_battery_level=25)

# Сценарій 1: Критична батарея 
(очікуємо високий ризик)
risk = 
monitor.compute_risk_score(battery=10,link_state="NORMAL", severe_count=0, critical_count=0)
  assert risk >=5, f"Помилка! Ризик має бути високим при батареї 10%, отримано: {risk}"
#Сценарій 2: Втрата зв'язку
(FAILSAFE)
risk = monitor.compute_risk_score(battery=80,link_state="FAILSAFE", severe_count=0,
                                  critscal_count=0)
  assert risk >= 4, f"Помилка! FAILSAFE повинен значно підвищувати ризики, отримано: {risk}"
  print("Усі тести пройдено успішно!")
if _name_=="_main_":
   test_risk_assessment()
