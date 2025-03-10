import agentpy as ap
import numpy as np
from flask import Flask, jsonify
import threading

app = Flask(__name__)

# ------------------------------
# Agente Coche (CarAgent)
# ------------------------------
class CarAgent(ap.Agent):
    def setup(self):
        """Inicializa el auto con gasolina y aprendizaje por refuerzo"""
        self.fuel = np.random.randint(50, 100)  # Nivel de gasolina aleatorio
        self.pos = None  # Se asigna en el modelo
        self.q_table = {}  # Tabla Q-Learning
        self.learning_rate = 0.1  # α
        self.discount_factor = 0.9  # γ
        self.epsilon = 0.2  # Probabilidad de exploración

    def choose_action(self, fuel_level, station_status):
        """Escoge la mejor acción basado en Q-Learning"""
        actions = ["WAIT", "GO_TO_NEAREST", "FIND_ANOTHER"]
        state = (fuel_level, station_status)

        if state not in self.q_table:
            self.q_table[state] = {a: 0 for a in actions}

        if np.random.rand() < self.epsilon:
            return np.random.choice(actions)  # Exploración
        else:
            return max(self.q_table[state], key=self.q_table[state].get)  # Explotación

    def update_q_values(self, state, action, reward, new_state):
        """Actualiza la Q-table después de tomar una acción"""
        max_future_q = max(self.q_table[new_state].values(), default=0)
        current_q = self.q_table[state][action]

        self.q_table[state][action] = current_q + self.learning_rate * (
            reward + self.discount_factor * max_future_q - current_q
        )

    def move(self):
        """Decide moverse o recargar gasolina"""
        fuel_level = "LOW" if self.fuel < 20 else "MEDIUM" if self.fuel < 50 else "HIGH"
        station_status = self.model.get_station_status(self)

        action = self.choose_action(fuel_level, station_status)

        if action == "GO_TO_NEAREST":
            self.fuel -= 5  # Gasta gasolina al moverse
            self.model.grid.move_by(self, (np.random.choice([-1, 1]), 0))  # Movimiento en la cuadrícula
        elif action == "FIND_ANOTHER":
            self.fuel -= 3  # Gasta menos, pero busca otra estación
        elif action == "WAIT":
            self.fuel -= 1  # Consume gasolina en espera

        reward = 3 if action == "GO_TO_NEAREST" and station_status == "FREE" else -2
        if self.fuel <= 0:
            reward = -5  # Penalización si se queda sin gasolina

        new_state = (fuel_level, station_status)
        self.update_q_values((fuel_level, station_status), action, reward, new_state)

# ------------------------------
# Agente Semáforo (TrafficLightAgent)
# ------------------------------
class TrafficLightAgent(ap.Agent):
    def setup(self):
        """Inicializa el semáforo con aprendizaje Q-Learning"""
        self.state = "RED"
        self.wait_time = 5  # Tiempo inicial en cada estado
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.2

    def choose_action(self, num_cars_waiting):
        """El semáforo decide si cambiar a verde o mantenerse en rojo"""
        actions = ["KEEP_RED", "CHANGE_TO_GREEN"]

        if num_cars_waiting not in self.q_table:
            self.q_table[num_cars_waiting] = {a: 0 for a in actions}

        if np.random.rand() < self.epsilon:
            return np.random.choice(actions)
        else:
            return max(self.q_table[num_cars_waiting], key=self.q_table[num_cars_waiting].get)

    def step(self):
        """Ejecuta un ciclo de decisión"""
        num_cars_waiting = self.model.get_cars_waiting(self)
        action = self.choose_action(num_cars_waiting)

        if action == "CHANGE_TO_GREEN":
            self.state = "GREEN"
            reward = 5 if num_cars_waiting > 3 else -2
        else:
            self.state = "RED"
            reward = -5 if num_cars_waiting > 3 else 2

        self.q_table[num_cars_waiting][action] += self.learning_rate * (
            reward + self.discount_factor * max(self.q_table[num_cars_waiting].values(), default=0) - self.q_table[num_cars_waiting][action]
        )

# ------------------------------
# Agente Gasolinera (GasStationAgent)
# ------------------------------
class GasStationAgent(ap.Agent):
    def setup(self):
        """Define la gasolinera con una capacidad limitada"""
        self.capacity = 2  # Máximo autos recargando
        self.current_cars = 0

    def refuel_car(self, car):
        """Recarga gasolina al auto"""
        if self.current_cars < self.capacity:
            car.fuel = 100
            self.current_cars += 1

    def step(self):
        """Reduce la cantidad de autos recargando en cada iteración"""
        if self.current_cars > 0:
            self.current_cars -= 1

# ------------------------------
# Modelo de Tráfico (TrafficModel)
# ------------------------------
class TrafficModel(ap.Model):
    def setup(self):
        """Inicializa el grid, autos, semáforos y gasolineras"""
        self.grid = ap.Grid(self, (20, 20), track_empty=True)

        self.cars = ap.AgentList(self, 10, CarAgent)
        self.traffic_lights = ap.AgentList(self, 4, TrafficLightAgent)
        self.gas_stations = ap.AgentList(self, 3, GasStationAgent)

        self.grid.add_agents(self.cars, random=True)
        self.grid.add_agents(self.traffic_lights, random=True)
        self.grid.add_agents(self.gas_stations, random=True)

    def step(self):
        """Ejecuta un paso de la simulación"""
        self.cars.move()
        self.traffic_lights.step()
        self.gas_stations.step()

    def get_cars_waiting(self, traffic_light):
        """Devuelve cuántos autos están esperando en un semáforo"""
        return sum(1 for car in self.cars if self.grid.positions[car] in self.grid.positions[traffic_light])

    def get_station_status(self, car):
        """Verifica si una gasolinera está disponible"""
        for station in self.gas_stations:
            if self.grid.positions[station] in self.grid.positions[car]:
                return "FREE" if station.current_cars < station.capacity else "BUSY"
        return "NO_STATION"

# ------------------------------
# Servidor Flask para Simulación
# ------------------------------
traffic_model = TrafficModel()
traffic_model.setup()

@app.route('/simulate', methods=['GET'])
def run_simulation():
    """Ejecuta un paso y devuelve datos en JSON"""
    traffic_model.step()
    result = [{"id": i, "pos": list(agent.pos) if agent.pos else None} for i, agent in enumerate(traffic_model.cars)]
    return jsonify(result)

def run_flask():
    app.run(debug=True, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
