import agentpy as ap
import numpy as np
from flask import Flask, jsonify
import threading

app = Flask(__name__)

class CarAgent(ap.Agent):
    def setup(self):
        """Inicializa la velocidad y la posición del auto."""
        self.speed = np.random.choice([1, 2])  # Velocidad aleatoria
        self.pos = None  # Se asignará en el modelo

    def move(self):
        """Mueve el auto a una nueva posición, si es posible."""
        # 🔹 Verificar que el agente aún está en la cuadrícula antes de moverse
        if self not in self.model.grid.positions:
            print(f"Agent {self} not in grid positions.")  # Debugging information
            return  # Evita error si el agente ha sido eliminado del grid

        current_pos = self.model.grid.positions.get(self, None)  # Obtener la posición actual
        print(f"Current position of agent {self}: {current_pos}")  # Debugging information

        # 🔹 Evitar errores si la posición actual ya no existe en el grid
        if current_pos is None or current_pos not in self.model.grid.positions:
            print(f"Agente {self} tiene una posición inválida.")  # Debug
            return  

        # 🔹 Obtener movimientos válidos (asegurar que la posición existe)
        possible_moves = self.model.grid.neighbors(current_pos, distance=self.speed)
        print(f"Possible moves for agent {self}: {possible_moves}")  # Debugging information

        possible_moves = [pos for pos in possible_moves if pos in self.model.grid.positions.values()]

        if possible_moves:
            new_pos = self.random.choice(possible_moves)
            print(f"Agente {self} se mueve de {current_pos} a {new_pos}")  # Debug

            # 🔹 Verificar que la nueva posición aún existe antes de moverse
            if new_pos in self.model.grid.positions.values():
                self.model.grid.move_to(self, new_pos)

                # 🔹 Asegurar que el agente sigue en la cuadrícula después de moverse
                if self in self.model.grid.positions:
                    self.pos = self.model.grid.positions[self]
                else:
                    self.pos = None  # En caso de que el agente haya sido eliminado
        else:
            print(f"Agente {self} no encontró movimiento válido.")  # Debug
            self.pos = current_pos  # 🔹 Mantener posición actual si no hay movimientos válidos

class TrafficModel(ap.Model):
    def setup(self):
        """Inicializa la cuadrícula y los autos en posiciones aleatorias."""
        self.grid = ap.Grid(self, (20, 20), track_empty=True)  # Definir la cuadrícula
        self.agents = ap.AgentList(self, 10, CarAgent)  # Crear 10 autos
        self.grid.add_agents(self.agents, random=True)  # Asignar posiciones válidas a los agentes

        for agent in self.agents:
            agent.pos = self.grid.positions.get(agent, None)  # Asignar posición inicial válida

    def step(self):
        """Ejecuta un paso de la simulación y devuelve las posiciones."""
        print("Moviendo autos en el grid...")  # Debug
        self.agents.move()
        return [{"id": i, "pos": list(agent.pos) if agent.pos else None} for i, agent in enumerate(self.agents)]

# ✅ Crear el modelo y asegurarse de ejecutar setup()
traffic_model = TrafficModel()
traffic_model.setup()  # 🔹 ¡Esta línea es clave!

@app.route('/simulate', methods=['GET'])
def run_simulation():
    """Avanza la simulación en un paso y envía los datos actualizados en formato JSON."""
    print("Ejecutando un paso de la simulación...")  # Debug
    result = traffic_model.step()
    print("Datos actualizados:", result)  # Debug
    return jsonify(result)

def run_flask():
    app.run(debug=True, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
