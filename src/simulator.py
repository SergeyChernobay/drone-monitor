import time
import logging
from drone_monitor import DroneMonitor

def run_simulation():
    logging.info("=== Запуск Симулятора Польоту ===")
    drone = DroneMonitor(drone_name="Стелс-1")
    
    # Сценарій: 5 кроків (секунд) польоту з поступовим погіршенням умов (вплив РЕБ + розряд)
    telemetry_data = [
        {"battery": 80, "alt": 100, "sig": 90, "gps": (50.4, 30.5)}, # Норма
        {"battery": 79, "alt": 100, "sig": 50, "gps": (50.4, 30.5)}, # Падіння сигналу
        {"battery": 78, "alt": 100, "sig": 20, "gps": (50.4, 30.5)}, # Сильний вплив РЕБ
        {"battery": 20, "alt": 100, "sig": 10, "gps": (50.4, 30.5)}, # РЕБ + Критична батарея
        {"battery": 10, "alt": 100, "sig": 0,  "gps": (50.4, 30.5)}  # Повна втрата
    ]
    
    for i, data in enumerate(telemetry_data, 1):
        logging.info(f"\n--- Секунда польоту {i} ---")
        drone.check_telemetry(data["battery"], data["alt"], data["sig"], data["gps"])
        time.sleep(1) # Затримка 1 секунда для реалістичності

if __name__ == "__main__":
    run_simulation()
