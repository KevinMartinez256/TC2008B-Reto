import agentpy as ap
import numpy as np
from flask import Flask, jsonify
import threading

app = Flask(__name__) # Crear una aplicación Flask para manejar solicitudes HTTP

# Clase que representa un agente coche
class CarAgent(ap.Agent):
    def setup(self):
        self.speed = 1 # Velocidad del coche (no usada directamente en este código)
        self.pos = None # Posición actual del coche en la grilla
        self.fuel = 100 # Nivel inicial de combustible
        self.state = "WAITING" # Estado inicial del coche
        self.path = [] # Lista de posiciones por recorrer en el paso actual
        self.route = [] # Ruta completa del coche
        self.route_index = 0 # Índice actual en la ruta
        self.active = False # Indica si el coche está activo en la simulación

    # Asignar una ruta al coche
    def set_route(self, route):
        self.route = route # Guardar la ruta completa
        self.path = route.copy() # Copiar la ruta para el movimiento paso a paso
        self.pos = self.route[0] if self.route else None # Establecer posición inicial
        self.route_index = 0 # Reiniciar el índice de ruta
        print(f"Agente {self.id} recibió ruta: {route}. Longitud de la ruta: {len(route)}")

    # Lógica de movimiento del coche
    def move(self):
        if not self.active: # Si no está activo, no hacer nada
            return

        # Si el coche no está en la grilla, moverlo a la posición inicial
        if self not in self.model.grid.positions:
            self.model.grid.move_to(self, self.route[0])
            self.pos = self.route[0]
            print(f"Agente {self.id} reiniciado en {self.pos}")

        self.fuel -= 1 # Reducir el combustible en cada paso
        # Obtener posiciones ocupadas por otros agentes activos
        occupied_positions = list(set(tuple(self.model.grid.positions[agent]) for agent in self.model.agents if agent != self and agent.active))
        print(f"Agente {self.id} en {self.pos}, combustible: {self.fuel}, estado: {self.state}. Índice de ruta: {self.route_index}. Ruta actual: {self.path}. Posiciones ocupadas: {occupied_positions}")

        # Si está esperando, cambiar a MOVING y salir
        if self.state == "WAITING":
            self.state = "MOVING"
            return

        # Si no hay más pasos en el camino actual, avanzar al siguiente punto de la ruta
        if not self.path:
            self.route_index = (self.route_index + 1) % len(self.route)
            self.path = [self.route[self.route_index]]

        if self.path:
            next_pos = self.path[0] # Próxima posición a la que moverse

            # Verificar si hay un semáforo en la próxima posición
            traffic_light = next((tl for tl in self.model.traffic_lights if tuple(tl.pos) == tuple(next_pos)), None)
            if traffic_light and traffic_light.state == "RED":
                self.state = "WAITING" # Detenerse si el semáforo está en rojo
                print(f"Agente {self.id} detenido por semáforo rojo en {next_pos}")
                return

            # Si el combustible es bajo y está en una gasolinera, recargar
            if self.fuel < 20 and tuple(next_pos) == tuple(self.model.gas_stations[0].pos) and self.state != "REFUELING":
                self.state = "REFUELING"
                print(f"Agente {self.id} llegando a la gasolinera en {next_pos}")

            # Recargar combustible si está en la gasolinera
            if self.state == "REFUELING" and tuple(self.pos) == tuple(self.model.gas_stations[0].pos):
                self.fuel += 50
                if self.fuel >= 100:
                    self.fuel = 100 # Limitar el combustible a 100
                    self.state = "MOVING" # Volver a moverse tras recargar
                    print(f"Agente {self.id} recargado en la gasolinera, regresando a MOVING")

            # Si la próxima posición está ocupada, esperar
            if tuple(next_pos) in occupied_positions:
                print(f"Agente {self.id} esperando: posición {next_pos} ocupada")
                return

            # Intentar mover el coche a la próxima posición
            try:
                self.model.grid.move_to(self, next_pos)
                self.pos = next_pos # Actualizar posición
                self.path.pop(0) # Eliminar el paso completado
                self.route_index = (self.route_index + 1) % len(self.route) # Avanzar en la ruta
                print(f"Agente {self.id} se movió a {next_pos}")
            except Exception as e:
                print(f"Error al mover el agente {self.id} a {next_pos}: {e}")

# Clase que representa un semáforo
class TrafficLightAgent(ap.Agent):
    def setup(self):
        self.state = "RED" # Estado inicial del semáforo
        self.pos = None # Posición del semáforo en la grilla
        self.timer = 3 # Temporizador para cambiar de estado

    # Actualizar el estado del semáforo
    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.state = "GREEN" if self.state == "RED" else "RED" # Cambiar entre rojo y verde
            self.timer = 3 # Reiniciar el temporizador
            print(f"Semáforo en {self.pos} cambió a {self.state}")

# Clase que representa una gasolinera
class GasStationAgent(ap.Agent):
    def setup(self):
        self.state = "AVAILABLE" # Estado inicial de la gasolinera
        self.pos = None # Posición de la gasolinera en la grilla

    def refuel(self, car):
        if self.state == "AVAILABLE": # Si está disponible, permitir recarga
            self.state = "BUSY"
            return True
        return False

    def release(self):
        self.state = "AVAILABLE" # Liberar la gasolinera

# Modelo principal de la simulación de tráfico
class TrafficModel(ap.Model):
    def setup(self):
        self.grid = ap.Grid(self, (200, 200), track_empty=True) # Crear una grilla de 200x200
        self.agents = ap.AgentList(self, 5, CarAgent) # Crear 5 agentes coche
        self.traffic_lights = ap.AgentList(self, 2, TrafficLightAgent) # Crear 2 semáforos
        self.gas_stations = ap.AgentList(self, 1, GasStationAgent) # Crear 1 gasolinera

        # Definir una ruta fija para todos los coches
        route1 = [
            (-9, -5), (0, -17), (-1, -23), (-11, -23), (-56, -23), (-96, -23), (-107, -23), (-111, -20),
            (-116, -20), (-120, -20), (-123, -23), (-123, -27), (-119, -32), (-114, -32), (-110, -30),
            (-106, -28), (-62, -29), (-8, -29), (26, -29)
        ]

        # Asignar la misma ruta a todos los agentes
        for agent in self.agents:
            agent.set_route(route1)

        # Posiciones iniciales de los coches (todos comienzan en el mismo punto)
        initial_positions = [(-9, -5)] * 5
        self.grid.add_agents(self.agents, initial_positions)

        # Configurar posiciones de los semáforos
        self.traffic_lights[0].pos = (-9, -5)
        self.traffic_lights[1].pos = (0, -17)
        self.grid.add_agents(self.traffic_lights, [tl.pos for tl in self.traffic_lights])

        # Configurar posición de la gasolinera
        self.gas_stations[0].pos = (-1, -23)
        self.grid.add_agents(self.gas_stations, [gs.pos for gs in self.gas_stations])

        # Mostrar posiciones iniciales de los agentes
        for i, agent in enumerate(self.agents):
            agent.pos = self.grid.positions[agent]
            print(f"Agente {agent.id} comienza en {agent.pos}")

        self.step_count = 0 # Contador de pasos
        self.time_since_start = 0.0 # Tiempo transcurrido desde el inicio
        self.dt = 0.5 # Intervalo de tiempo por paso (en segundos)
        self.active_agents = 0 # Contador de agentes activos

    # Lógica de cada paso de la simulación
    def step(self):
        self.step_count += 1 # Incrementar el contador de pasos
        self.time_since_start = self.step_count * self.dt # Actualizar el tiempo transcurrido

        # Activar agentes gradualmente cada 3 segundos
        if self.active_agents < 5 and self.time_since_start >= self.active_agents * 3:
            self.agents[self.active_agents].active = True
            print(f"Activando agente {self.agents[self.active_agents].id} en t={self.time_since_start}")
            self.active_agents += 1

        self.traffic_lights.update() # Actualizar los semáforos
        self.agents.move() # Mover los coches

        # Preparar datos de los agentes activos para enviar a Unity
        result = [
            {
                "id": i,
                "pos": list(agent.pos) if agent.pos else [0, 0], # Posición actual
                "state": agent.state, # Estado del coche
                "fuel": agent.fuel, # Nivel de combustible
                "route_index": agent.route_index, # Índice actual en la ruta
                "route_indices": list(range(agent.route_index, len(agent.route))) # Índices restantes de la ruta
            }
            for i, agent in enumerate(self.agents) if agent.active
        ]
        print(f"Enviando a Unity: {result}")
        return result

# Crear e inicializar el modelo de tráfico
traffic_model = TrafficModel()
traffic_model.setup()

# Ruta HTTP para que Unity solicite datos de la simulación
@app.route('/simulate', methods=['GET'])
def run_simulation():
    result = traffic_model.step() # Ejecutar un paso de la simulación
    print(f"Enviando a Unity: {result}")
    return jsonify(result) # Devolver los datos en formato JSON

# Función para ejecutar el servidor Flask en un hilo separado
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

# Iniciar el servidor Flask en un hilo
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()