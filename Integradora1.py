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
            print(f"❌ Agente {self} ya no está en el grid, no puede moverse.")  
            return  

        current_pos = self.model.grid.positions.get(self, None)

        # 🔹 Evitar errores si la posición actual no es válida
        if current_pos is None or current_pos not in self.model.grid.positions.values():
            print(f"⚠️ Agente {self} tiene una posición inválida y no puede moverse.")  
            return  

        # 🔹 Obtener movimientos válidos dentro de los límites de la cuadrícula
        try:
            possible_moves = [
                pos for pos in self.model.grid.neighbors(current_pos, distance=1)
                if pos in self.model.grid.positions.values()
            ]
        except KeyError:
            print(f"❌ ERROR: `neighbors()` intentó acceder a una posición inexistente para {self}.")  
            self.pos = current_pos  # Mantener la posición anterior
            return

        print(f"🔄 Agente {self} en {current_pos} tiene posibles movimientos: {possible_moves}")  

        if possible_moves:
            new_pos = self.random.choice(possible_moves)
            print(f"✅ Agente {self} intenta moverse de {current_pos} a {new_pos}")  

            # 🔹 Verificar que la nueva posición aún existe antes de moverse
            try:
                self.model.grid.move_to(self, new_pos)

                # 🔹 Asegurar que el agente sigue en la cuadrícula después de moverse
                if self in self.model.grid.positions:
                    self.pos = self.model.grid.positions[self]
                else:
                    print(f"⚠️ Agente {self} fue eliminado después de moverse.")  
                    self.pos = None  
            except KeyError:
                print(f"❌ ERROR: Intento de mover a {self} a una posición inválida {new_pos}.")  
                self.pos = current_pos  # Mantener la posición anterior
        else:
            print(f"🚫 Agente {self} no encontró movimiento válido y se queda en {current_pos}.")  
            self.pos = current_pos  # Mantener posición actual si no hay movimientos válidos

class TrafficModel(ap.Model):
    def setup(self):
        """Inicializa la cuadrícula y los autos en posiciones aleatorias."""
        self.grid = ap.Grid(self, (20, 20), track_empty=True)  
        self.agents = ap.AgentList(self, 10, CarAgent)  

        # 🔹 Asignar posiciones válidas a los agentes
        self.grid.add_agents(self.agents, random=True)

        for agent in self.agents:
            agent.pos = self.grid.positions.get(agent, None)  

    def step(self):
        """Ejecuta un paso de la simulación y devuelve las posiciones."""
        print("🔄 Moviendo autos en el grid...")  
        self.agents.move()
        return [{"id": i, "pos": list(agent.pos) if agent.pos else None} for i, agent in enumerate(self.agents)]

# ✅ Crear el modelo y asegurarse de ejecutar setup()
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
