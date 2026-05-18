import numpy as np
import random
from environment import BatteryEnvironment

class QLearningAgent:
    def __init__(self, env, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_decay=0.998, min_epsilon=0.01):
        self.env = env
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.q_table = {}
        
    def get_q_values(self, state):
        if state not in self.q_table:
            # Initialize with zeros
            self.q_table[state] = np.zeros(3)
        return self.q_table[state]
        
    def choose_action(self, state, train_mode=True):
        if train_mode and random.uniform(0, 1) < self.epsilon:
            return random.randint(0, 2)
        else:
            q_values = self.get_q_values(state)
            max_q = np.max(q_values)
            # Find all actions with max Q-value to break ties randomly
            best_actions = [a for a in range(3) if q_values[a] == max_q]
            return random.choice(best_actions)
            
    def update_q_table(self, state, action, reward, next_state):
        q_values = self.get_q_values(state)
        next_q_values = self.get_q_values(next_state)
        
        best_next_q = np.max(next_q_values)
        
        # Q-Learning update rule
        q_values[action] = q_values[action] + self.alpha * (reward + self.gamma * best_next_q - q_values[action])
        
    def train(self, episodes=2000, steps_per_episode=168): # 168 hours = 7 days
        for episode in range(episodes):
            state = self.env.reset()
            total_reward = 0
            
            for step in range(steps_per_episode):
                action = self.choose_action(state, train_mode=True)
                next_state, reward, done, _ = self.env.step(action)
                
                self.update_q_table(state, action, reward, next_state)
                
                state = next_state
                total_reward += reward
                
            if self.epsilon > self.min_epsilon:
                self.epsilon *= self.epsilon_decay
                
        self.is_trained = True
                

if __name__ == "__main__":
    env = BatteryEnvironment()
    # High gamma (0.99) is CRITICAL to avoid the discounting trap over long wait periods (e.g., waiting 10h to discharge)
    agent = QLearningAgent(env, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_decay=0.998, min_epsilon=0.01)
    
    print("Starting training...")
    agent.train(episodes=2000, steps_per_episode=168) # Simulate 7 days per episode
    print("Training complete.\n")
    
    print("Testing the trained agent for 1 typical day (24 hours):")
    state = env.reset()
    total_test_reward = 0
    for hour in range(24):
        q_values = agent.get_q_values(state)
        # Always exploit during testing
        max_q = np.max(q_values)
        best_actions = [a for a in range(3) if q_values[a] == max_q]
        action = random.choice(best_actions)
        
        next_state, reward, done, _ = env.step(action)
        
        action_str = ["Hold", "Charge", "Discharge"][action]
        tariff_str = {0: "Cheap (1.0)", 1: "Mid (2.5)", 2: "Peak (5.0)"}[state[1]]
        
        print(f"Hour {state[0]:02d}:00 | Tariff: {tariff_str:<11} | SOC: {state[2]:>2d} | Action: {action_str:<9} | Reward: {reward:+.1f}")
        
        state = next_state
        total_test_reward += reward
        
    print(f"\nTotal test reward for 24h: {total_test_reward:.2f}")
