using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.Networking;

public class TrafficManager : MonoBehaviour
{
    public GameObject carPrefab; // Prefab del coche que se instanciará en la simulación
    public WaypointManager waypointManager; // Referencia al manejador de waypoints
    private Dictionary<int, GameObject> cars = new Dictionary<int, GameObject>(); // Diccionario para rastrear los coches por su ID

    void Start()
    {
        // Si no se asignó un WaypointManager en el Inspector, buscar uno en la escena
        if (waypointManager == null)
        {
            waypointManager = FindFirstObjectByType<WaypointManager>();
        }

        // Verificar que WaypointManager exista, si no, mostrar error
        if (waypointManager == null)
        {
            Debug.LogError("🚨 Error: WaypointManager no encontrado en la escena. Asegúrate de que está presente y tiene el script WaypointManager adjunto.");
            return;
        }

        // Verificar que carPrefab esté asignado en el Inspector
        if (carPrefab == null)
        {
            Debug.LogError("🚨 Error: carPrefab no está asignado en el Inspector.");
            return;
        }

        // Mostrar información inicial sobre los waypoints si existen
        if (waypointManager.waypoints != null && waypointManager.waypoints.Count > 0)
        {
            Debug.Log($"Primer waypoint encontrado en {waypointManager.waypoints[0].position}. Total de waypoints: {waypointManager.waypoints.Count}.");
        }
        else
        {
            Debug.LogError("🚨 No se encontraron waypoints en WaypointManager. Verifica el script y la jerarquía.");
        }

        // Iniciar la corrutina que actualiza el tráfico periódicamente
        StartCoroutine(UpdateTraffic());
    }

    // Corrutina que consulta datos de AgentPy y actualiza los coches en Unity
    IEnumerator UpdateTraffic()
    {
        while (true) // Bucle infinito para mantener la simulación activa
        {
            // Hacer una solicitud HTTP GET al servidor Flask en localhost:5000/simulate
            UnityWebRequest request = UnityWebRequest.Get("http://127.0.0.1:5000/simulate");
            yield return request.SendWebRequest(); // Esperar a que la solicitud se complete

            // Si la solicitud fue exitosa
            if (request.result == UnityWebRequest.Result.Success)
            {
                string json = request.downloadHandler.text; // Obtener los datos en formato JSON
                Debug.Log($"📥 Datos recibidos de AgentPy: {json}");

                // Deserializar el JSON en un arreglo de objetos CarData
                CarData[] carDataArray = JsonHelper.FromJson<CarData>(json);

                // Procesar cada coche recibido del servidor
                foreach (CarData car in carDataArray)
                {
                    Debug.Log($"🚗 Procesando coche {car.id} - Estado: {car.state} - Combustible: {car.fuel} - Índice de ruta: {car.route_index}");

                    // Si el coche está en estado "WAITING", no se crea ni actualiza
                    if (car.state == "WAITING")
                    {
                        Debug.Log($"Coche {car.id} está en estado WAITING, omitiendo creación/actualización.");
                        continue;
                    }

                    // Si el coche no existe en el diccionario, crearlo
                    if (!cars.ContainsKey(car.id))
                    {
                        // Determinar la posición inicial basada en el índice de ruta
                        Vector3 initialPosition = (waypointManager.waypoints != null && waypointManager.waypoints.Count > 0)
                            ? waypointManager.waypoints[car.route_index].position
                            : Vector3.zero;
                        GameObject newCar = Instantiate(carPrefab, initialPosition, Quaternion.identity); // Instanciar el coche
                        newCar.name = $"Car_{car.id}"; // Asignar un nombre único
                        cars[car.id] = newCar; // Añadir al diccionario

                        newCar.transform.position = initialPosition; // Asegurar la posición inicial
                        Debug.Log($"✅ Creado {newCar.name} en {initialPosition}. Posición actual después de instanciar: {newCar.transform.position}");
                    }

                    // Obtener o añadir el componente PathFollower al coche
                    PathFollower pathFollower = cars[car.id].GetComponent<PathFollower>();
                    if (pathFollower == null)
                    {
                        pathFollower = cars[car.id].AddComponent<PathFollower>();
                        Debug.Log($"✅ PathFollower agregado a {cars[car.id].name}");
                    }

                    // Actualizar el estado y la ruta del coche si PathFollower y WaypointManager están disponibles
                    if (pathFollower != null && waypointManager != null)
                    {
                        pathFollower.SetCarState(car.state); // Actualizar el estado del coche

                        // Si el coche no tiene una ruta asignada, configurarla
                        if (!pathFollower.HasPath())
                        {
                            List<Transform> route = new List<Transform>(); // Lista para almacenar la ruta

                            // Verificar si los índices de ruta son válidos
                            if (car.route_indices == null || car.route_indices.Length == 0)
                            {
                                Debug.LogWarning($"⚠️ Coche {car.id} tiene una ruta nula desde AgentPy. Verifica la configuración de AgentPy.");
                            }
                            else
                            {
                                Debug.Log($"🔍 Ruta recibida para coche {car.id}: {string.Join("; ", car.route_indices)}");
                                // Iterar sobre los índices de waypoints enviados por AgentPy
                                foreach (int index in car.route_indices)
                                {
                                    if (index >= 0 && index < waypointManager.waypoints.Count)
                                    {
                                        Transform waypoint = waypointManager.waypoints[index];
                                        if (waypoint != null && !route.Contains(waypoint))
                                        {
                                            route.Add(waypoint); // Añadir waypoint a la ruta
                                            Debug.Log($"Waypoint {index} agregado en {waypoint.position}");
                                        }
                                        else
                                        {
                                            Debug.LogWarning($"⚠️ Waypoint en índice {index} es nulo.");
                                        }
                                    }
                                    else
                                    {
                                        Debug.LogWarning($"⚠️ Índice de waypoint {index} fuera de rango (total waypoints: {waypointManager.waypoints.Count}).");
                                    }
                                }
                            }

                            Debug.Log($"🔄 Coche {car.id} recibió {route.Count} waypoints desde AgentPy.");

                            // Asignar la ruta al PathFollower si hay waypoints válidos
                            if (route.Count > 0)
                            {
                                pathFollower.SetPath(route);
                                Debug.Log($"Ruta asignada con éxito a {cars[car.id].name} con {route.Count} waypoints.");
                            }
                            else
                            {
                                Debug.LogError($"🚨 No se pudo asignar una ruta válida al coche {car.id}. Verifica los índices enviados por AgentPy.");
                            }
                        }
                        else
                        {
                            Debug.Log($"Coche {car.id} ya tiene una ruta asignada, actualizando solo el estado.");
                        }
                    }
                    else
                    {
                        Debug.LogError($"🚨 Error: PathFollower no encontrado en {cars[car.id].name} o WaypointManager nulo.");
                    }
                }
            }
            else
            {
                Debug.LogError("❌ Error en la solicitud HTTP: " + request.error); // Mostrar error si la solicitud falla
            }

            yield return new WaitForSeconds(0.5f); // Esperar 0.5 segundos antes de la próxima actualización
        }
    }

    // Clase serializable para representar los datos de un coche recibidos desde AgentPy
    [System.Serializable]
    public class CarData
    {
        public int id; // Identificador único del coche
        public int[] pos; // Posición actual (no usada directamente en este código)
        public string state; // Estado del coche (WAITING, MOVING, REFUELING)
        public int fuel; // Nivel de combustible
        public int route_index; // Índice actual en la ruta
        public int[] route_indices; // Lista de índices de waypoints en la ruta
    }

    // Clase auxiliar para deserializar JSON en arreglos
    public static class JsonHelper
    {
        public static T[] FromJson<T>(string json)
        {
            string newJson = "{\"array\":" + json + "}"; // Envolver el JSON en un objeto para usar JsonUtility
            Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);
            return wrapper?.array ?? new T[0]; // Devolver el arreglo o un arreglo vacío si falla
        }

        [System.Serializable]
        private class Wrapper<T>
        {
            public T[] array; // Arreglo envuelto para deserialización
        }
    }
}