import logging
from collections import deque

# --- НАЛАШТУВАННЯ ЛОГЕРА ("Чорна скринька") ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

class DroneMonitor:
    def __init__(self,
                 drone_name="Тест-Дрон",
                 safe_battery_level=25,
                 window_size=10,
                 warn_thr=30,
                 severe_thr=15,
                 critical_thr=5,
                 degraded_enter=6,
                 degraded_exit=3,
                 failsafe_enter_severe=8,
                 failsafe_exit_severe=4,
                 failsafe_enter_critical=3):

        self.drone_name = drone_name
        self.safe_battery_level = safe_battery_level
        self.current_connection = "SIM1"
        self.backup_connection = "SIM2"
        self.home_coords = (50.4501, 30.5234)

        self.warn_thr = warn_thr
        self.severe_thr = severe_thr
        self.critical_thr = critical_thr

        self.level_history = deque(maxlen=window_size)

        self.degraded_enter = degraded_enter
        self.degraded_exit = degraded_exit
        self.failsafe_enter_severe = failsafe_enter_severe
        self.failsafe_exit_severe = failsafe_exit_severe
        self.failsafe_enter_critical = failsafe_enter_critical

        self.link_state = "NORMAL" 

    def _signal_level(self, signal_strength: int) -> int:
        if signal_strength < self.critical_thr:
            return 3
        if signal_strength < self.severe_thr:
            return 2
        if signal_strength < self.warn_thr:
            return 1
        return 0

    def _update_link_state(self, signal_strength: int):
        lvl = self._signal_level(signal_strength)
        self.level_history.append(lvl)

        warning_count = sum(1 for x in self.level_history if x >= 1)
        severe_count = sum(1 for x in self.level_history if x >= 2)
        critical_count = sum(1 for x in self.level_history if x >= 3)

        if self.link_state != "FAILSAFE":
            if severe_count >= self.failsafe_enter_severe or critical_count >= self.failsafe_enter_critical:
                self.link_state = "FAILSAFE"
        else:
            if severe_count <= self.failsafe_exit_severe and critical_count == 0:
                self.link_state = "DEGRADED_LINK" if warning_count >= self.degraded_exit else "NORMAL"

        if self.link_state != "FAILSAFE":
            if self.link_state == "NORMAL" and warning_count >= self.degraded_enter:
                self.link_state = "DEGRADED_LINK"
            elif self.link_state == "DEGRADED_LINK" and warning_count <= self.degraded_exit:
                self.link_state = "NORMAL"

        return self.link_state, warning_count, severe_count, critical_count, lvl

    def compute_risk_score(self, battery, link_state, severe_count, critical_count):
        """Аналітичний центр: оцінка ризиків на основі телеметрії."""
        risk = 0
        if battery < self.safe_battery_level:
            risk += 5
        elif battery < self.safe_battery_level + 10:
            risk += 2
            
        link_priority = {"DEGRADED_LINK": 2, "FAILSAFE": 4}
        risk += link_priority.get(link_state, 0)
        risk += (severe_count * 0.5) + (critical_count * 1.5)
        
        return risk

    def decide_action(self, risk):
        if risk < 2: return "NORMAL"
        elif risk < 4: return "DEGRADED"
        elif risk < 6: return "FAILSAFE"
        else: return "RTL"

    def switch_connection_mode(self, signal_strength, current_gps, force_autonomous=False):
        logging.info(f"Спроба перемикання. Сигнал: {signal_strength}%. Поточний: {self.current_connection}")

        if force_autonomous:
            msg = f"FAILSAFE: Автономний режим -> база {self.home_coords} | GPS={current_gps}"
            logging.critical(msg)
            return 4, msg

        if self.current_connection == "SIM1":
            self.current_connection = self.backup_connection
            msg = f"Переключено на резервний звʼязок: {self.current_connection}"
            logging.warning(msg)
            return 3, msg

        msg = f"Зв'язок втрачено повністю. Автономний режим -> база {self.home_coords}"
        logging.critical(msg)
        return 4, msg

    def check_telemetry(self, battery, altitude, signal_strength, current_gps):
        logging.info(f"Перевірка телеметрії: bat={battery}%, alt={altitude}м, sig={signal_strength}%, gps={current_gps}")

        if battery < self.safe_battery_level:
            msg = f"КРИТИЧНО! Батарея {battery}% (мінімум {self.safe_battery_level}%). Наказ: RTL."
            logging.critical(msg)
            return 2, msg

        state, w, s, c, lvl = self._update_link_state(signal_strength)
        lvl_name = {0: "OK", 1: "WARNING", 2: "SEVERE", 3: "CRITICAL"}[lvl]
        
        logging.debug(f"Стан лінку: {lvl_name} | Спрацювань: w={w}, s={s}, c={c} | FSM={state}")

        risk = self.compute_risk_score(battery, state, s, c)
        decision = self.decide_action(risk)
        
        logging.info(f"Аналіз ризику: score={risk:.2f} -> Рішення: {decision}")

        if decision == "RTL":
            msg = f"RTL ініційовано через високий ризик ({risk:.2f})"
            logging.critical(msg)
            return 2, msg

        if decision == "FAILSAFE":
            return self.switch_connection_mode(signal_strength, current_gps, force_autonomous=True)

        if decision == "DEGRADED":
            code, msg = self.switch_connection_mode(signal_strength, current_gps, force_autonomous=False)
            return (1 if code == 0 else code), f"DEGRADED: {msg}"

        msg = "Політ проходить у штатному режимі"
        logging.info(msg)
        return 0, msg

if __name__ == "__main__":
    drone = DroneMonitor(drone_name="Тест-Дрон", safe_battery_level=25)
    tests = [
        ("Критична батарея", 10, 300, 90, (50.40, 30.50)),
        ("Слабкий сигнал (warning)", 60, 300, 25, (50.41, 30.51)),
        ("Все OK", 70, 500, 80, (50.42, 30.52))
    ]

    for title, b, a, s, gps in tests:
        logging.info(f"--- Запуск сценарію: {title} ---")
        drone.check_telemetry(b, a, s, gps)
        print("-" * 40)
