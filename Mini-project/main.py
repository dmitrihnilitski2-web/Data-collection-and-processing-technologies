import uvicorn
import webbrowser
import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from environment import BatteryEnvironment
from agent import QLearningAgent

app = FastAPI(title="BESS RL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = BatteryEnvironment()
agent = QLearningAgent(env=env)


class TrainResponse(BaseModel):
    message: str
    episodes: int
    final_epsilon: float


class StepResponse(BaseModel):
    hour: int
    tariff: float
    load: float
    soc: float
    action: str
    reward: float
    savings: float


@app.post("/api/train", response_model=TrainResponse)
def train_agent(episodes: int = 1000):
    agent.train(episodes=episodes)
    return {
        "message": "Model trained successfully!",
        "episodes": episodes,
        "final_epsilon": agent.epsilon
    }


@app.get("/api/step", response_model=StepResponse)
def simulate_step():
    state = env.get_state()
    action = agent.choose_action(state, train_mode=False) if getattr(agent, 'is_trained', False) else 0

    _, _, _, info = env.step(action)
    action_map = {0: "Hold", 1: "Charge", 2: "Discharge"}

    return {
        "hour": info["hour"],
        "tariff": info["tariff"],
        "load": info["load"],
        "soc": info["soc"],
        "action": action_map[info["action_taken"]],
        "reward": info["reward"],
        "savings": info["savings"]
    }


# ВАЖЛИВО: Цей рядок має бути в самому кінці (після API),
# щоб FastAPI спочатку перевіряв /api/..., а потім віддавав файли сайту
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    def open_browser():
        time.sleep(1.5)  # Чекаємо півтори секунди, поки підніметься сервер
        webbrowser.open("http://127.0.0.1:8000")


    # Запускаємо відкриття браузера в окремому потоці
    threading.Thread(target=open_browser).start()

    # Запускаємо сам сервер (reload=False, бо ми запускаємо напряму)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)