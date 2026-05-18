import numpy as np

class BatteryEnvironment:
    def __init__(self):
        self.capacity = 10.0
        self.max_rw = 2.0 
        self.soc = 0.0
        self.hour = 0
        
    def reset(self):
        self.soc = 0.0
        self.hour = 0
        return self.get_state()
        
    def _get_tariff_level(self, hour):

        if hour >= 23 or hour < 7:
            return 0 
        elif 17 <= hour < 22:
            return 2  
        else:
            return 1 

    def _get_tariff_price(self, level):
        if level == 0: return 1.0
        if level == 1: return 2.5
        if level == 2: return 5.0

    def get_state(self):
        soc_discrete = int(round(self.soc))
        tariff_level = self._get_tariff_level(self.hour)
        return (self.hour, tariff_level, soc_discrete)

    def step(self, action):

        reward = 0
        current_hour = self.hour
        tariff_level = self._get_tariff_level(current_hour)
        tariff_price = self._get_tariff_price(tariff_level)
        soc_change = self.max_rw
        savings = 0.0
        
        if action == 1: 
            if self.soc + soc_change > self.capacity:
                reward = -100
            else:
                self.soc += soc_change
                if tariff_level == 0:
                    reward = 10 
                elif tariff_level == 1:
                    reward = -10
                elif tariff_level == 2:
                    reward = -50 
                savings = - (soc_change * tariff_price)
                    
        elif action == 2:
            if self.soc - soc_change < 0:
                reward = -100
            else:
                self.soc -= soc_change
                if tariff_level == 0:
                    reward = -50 
                elif tariff_level == 1:
                    reward = -10
                elif tariff_level == 2:
                    reward = 10
                savings = (soc_change * tariff_price)
                    
        elif action == 0: 
            reward = -0.1 

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
