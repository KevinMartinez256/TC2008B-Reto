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
        self.invalid_steps = 0  # Contador de pasos inválidos

    def move(self):
        """Mueve el auto a una nueva posición, si es posible."""
        # Verificar que el agente está en el grid
        if self not in self.model.grid.positions:
            print(f"❌ Agente {self} ya no está en el grid.")
            self.invalid_steps += 1
            if self.invalid_steps > 3:
                print(f"🚫 Agente {self} desactivado tras múltiples errores.")
            return

        current_pos = self.model.grid.positions.get(self)
        if current_pos is None:
            print(f"⚠️ Agente {self} tiene una posición inválida.")
            self.invalid_steps += 1
            if self.invalid_steps > 3:
                print(f"🚫 Agente {self} desactivado tras múltiples errores.")
            return

        # Resetear contador de errores
        self.invalid_steps = 0

        # Obtener vecinos manualmente para evitar accesos fuera del grid
        x, y = current_pos
        possible_moves = []
        grid_size = self.model.grid.shape  # Tamaño del grid (20, 20)

        # Definir movimientos válidos (arriba, abajo, izquierda, derecha)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            # Verificar que la nueva posición esté dentro del grid
            if 0 <= new_x < grid_size[0] and 0 <= new_y < grid_size[1]:
                possible_moves.append((new_x, new_y))

        if not possible_moves:
            print(f"🚫 Agente {self} no encontró movimientos válidos en {current_pos}.")
            return

        # Elegir una nueva posición aleatoria usando el random del modelo
        new_pos = self.model.random.choice(possible_moves)
        print(f"✅ Agente {self} se mueve de {current_pos} a {new_pos}")

        # Mover al agente a la nueva posición
        self.model.grid.move_to(self, new_pos)
        self.pos = new_pos

class TrafficModel(ap.Model):
    def setup(self):
        """Inicializa la cuadrícula y los autos en posiciones aleatorias."""
        self.grid = ap.Grid(self, (20, 20), track_empty=True)
        self.agents = ap.AgentList(self, 10, CarAgent)
        self.grid.add_agents(self.agents, random=True)

        # Asignar posiciones iniciales
        for agent in self.agents:
            agent.pos = self.grid.positions.get(agent)

    def step(self):
        """Ejecuta un paso de la simulación y devuelve las posiciones de los agentes activos."""
        print("🔄 Moviendo autos en el grid...")
        self.agents.move()
        return [{"id": i, "pos": list(agent.pos) if agent.pos else None} 
                for i, agent in enumerate(self.agents) if agent.invalid_steps <= 3]

# Crear y configurar el modelo
traffic_model = TrafficModel()
traffic_model.setup()

@app.route('/simulate', methods=['GET'])
def run_simulation():
    """Avanza la simulación en un paso y envía los datos actualizados en formato JSON."""
    print("🚀 Ejecutando un paso de la simulación...")
    result = traffic_model.step()
    print("📊 Datos actualizados:", result)
    return jsonify(result)

def run_flask():
    app.run(debug=True, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
