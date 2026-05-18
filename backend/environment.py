import numpy as np

class BatteryEnvironment:
    def __init__(self):
        self.capacity = 10.0
        self.max_rw = 2.0  # Amount of energy charged/discharged per step
        self.soc = 0.0
        self.hour = 0
        
    def reset(self):
        self.soc = 0.0
        self.hour = 0
        return self.get_state()
        
    def _get_tariff_level(self, hour):
        # 0: Cheap (23:00 - 07:00), 1: Mid (07:00-17:00, 22:00-23:00), 2: Peak (17:00 - 22:00)
        if hour >= 23 or hour < 7:
            return 0  # 1.0 ₴ - Cheap
        elif 17 <= hour < 22:
            return 2  # 5.0 ₴ - Peak
        else:
            return 1  # 2.5 ₴ - Mid

    def _get_tariff_price(self, level):
        if level == 0: return 1.0
        if level == 1: return 2.5
        if level == 2: return 5.0

    def get_state(self):
        soc_discrete = int(round(self.soc))
        tariff_level = self._get_tariff_level(self.hour)
        return (self.hour, tariff_level, soc_discrete)

    def step(self, action):
        # Actions: 0 = Hold, 1 = Charge, 2 = Discharge
        reward = 0
        current_hour = self.hour
        tariff_level = self._get_tariff_level(current_hour)
        tariff_price = self._get_tariff_price(tariff_level)
        soc_change = self.max_rw
        savings = 0.0
        
        if action == 1:  # Charge
            if self.soc + soc_change > self.capacity:
                reward = -100  # Strict penalty for overcharging
            else:
                self.soc += soc_change
                if tariff_level == 0:
                    reward = 10   # Big plus for charging at cheap
                elif tariff_level == 1:
                    reward = -10  # Penalty for charging at mid
                elif tariff_level == 2:
                    reward = -50  # Severe penalty for charging at peak
                savings = - (soc_change * tariff_price)
                    
        elif action == 2:  # Discharge
            if self.soc - soc_change < 0:
                reward = -100  # Strict penalty for overdischarging
            else:
                self.soc -= soc_change
                if tariff_level == 0:
                    reward = -50  # Severe penalty for discharging at cheap
                elif tariff_level == 1:
                    reward = -10  # Penalty for discharging at mid
                elif tariff_level == 2:
                    reward = 10   # Big plus for discharging at peak
                savings = (soc_change * tariff_price)
                    
        elif action == 0:  # Hold
            reward = -0.1  # Small penalty to avoid "sleeping" forever
            
        # Advance time
        self.hour = (self.hour + 1) % 24
        
        done = False
        
        info = {
            "hour": current_hour,
            "tariff": tariff_price,
            "load": 0.0,
            "soc": self.soc,
            "action_taken": action,
            "reward": reward,
            "savings": savings
        }
        
        return self.get_state(), reward, done, info
