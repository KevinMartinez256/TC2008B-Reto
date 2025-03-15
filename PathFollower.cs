using UnityEngine;
using System.Collections.Generic;

public class PathFollower : MonoBehaviour
{
    private List<Transform> waypoints = new List<Transform>(); // Lista de waypoints que el coche seguirá
    public float speed = 10f; // Velocidad de movimiento del coche
    public float rotationSpeed = 5f; // Velocidad de rotación del coche
    private int currentWaypointIndex = 0; // Índice del waypoint actual
    private bool hasTeleported = false; // Indica si el coche se ha teletransportado al inicio
    private string carState = "MOVING"; // Estado actual del coche
    private bool hasPath = false; // Indica si el coche tiene una ruta asignada
    private Rigidbody rb; // Referencia al componente Rigidbody para física

    // Verificar si el coche tiene una ruta asignada
    public bool HasPath()
    {
        return hasPath;
    }

    // Actualizar el estado del coche
    public void SetCarState(string state)
    {
        carState = state;
        Debug.Log($"Estado del coche {gameObject.name} actualizado a: {carState}");
    }

    void Start()
    {
        // Obtener el Rigidbody del coche
        rb = GetComponent<Rigidbody>();
        if (rb == null)
        {
            Debug.LogError("No se encontró un Rigidbody en el coche. Asegúrate de añadir uno.");
        }
        else
        {
            rb.freezeRotation = true; // Evitar rotaciones no deseadas por física
            rb.useGravity = true; // Mantener el coche en el suelo
        }
    }

    // Actualización basada en física (FixedUpdate)
    void FixedUpdate()
    {
        // Si no hay waypoints, no hacer nada
        if (waypoints == null || waypoints.Count == 0)
        {
            Debug.LogWarning($"No hay waypoints asignados para {gameObject.name}.");
            return;
        }

        // Si se alcanzó el final de la ruta, reiniciar
        if (currentWaypointIndex >= waypoints.Count)
        {
            Debug.Log($"Coche {gameObject.name} llegó al final de la ruta.");
            currentWaypointIndex = 0;
            hasTeleported = false;
            return;
        }

        // Si el coche está recargando, detener el movimiento
        if (carState == "REFUELING")
        {
            Debug.Log($"Coche {gameObject.name} recargando combustible en {waypoints[currentWaypointIndex].position}");
            return;
        }

        Transform target = waypoints[currentWaypointIndex]; // Waypoint objetivo
        Vector3 targetPosition = target.position; // Posición del waypoint
        Vector3 currentPosition = transform.position; // Posición actual del coche

        // Calcular la dirección y distancia al waypoint
        Vector3 direction = (targetPosition - currentPosition).normalized;
        float distance = Vector3.Distance(currentPosition, targetPosition);
        Debug.Log($"Moviendo {gameObject.name} hacia {target.position} (distancia: {distance}, dirección: {direction}, posición actual: {currentPosition}, waypoint actual: {currentWaypointIndex})");

        // Rotar suavemente hacia el waypoint
        if (direction.magnitude > 0.1f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(direction);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
        }

        // Teletransportar al inicio si la distancia es muy grande (solo al principio)
        if (distance > 100f && !hasTeleported && currentWaypointIndex == 0)
        {
            if (rb != null) rb.MovePosition(targetPosition); // Usar Rigidbody para mover
            else transform.position = targetPosition; // Mover directamente si no hay Rigidbody
            hasTeleported = true;
            Debug.Log($"Teletransportado {gameObject.name} a {targetPosition} para iniciar el movimiento.");
        }
        else
        {
            // Mover suavemente hacia el waypoint
            if (rb != null)
            {
                Vector3 velocity = direction * speed;
                rb.linearVelocity = Vector3.Lerp(rb.linearVelocity, velocity, Time.deltaTime * 5f); // Interpolación suave
            }
            else
            {
                transform.position += direction * speed * Time.deltaTime; // Movimiento sin física
            }
        }

        // Avanzar al siguiente waypoint si está lo suficientemente cerca
        if (distance < 1f)
        {
            currentWaypointIndex++;
            Debug.Log($"Coche {gameObject.name} avanzó al waypoint {currentWaypointIndex}/{waypoints.Count}");
        }
    }

    // Asignar una nueva ruta al coche
    public void SetPath(List<Transform> newPath)
    {
        waypoints = newPath; // Establecer la lista de waypoints
        currentWaypointIndex = 0; // Reiniciar el índice
        hasTeleported = false; // Reiniciar el estado de teletransporte
        hasPath = true; // Marcar que tiene una ruta
        if (waypoints != null && waypoints.Count > 0)
        {
            Debug.Log($"Ruta asignada a {gameObject.name} con {waypoints.Count} waypoints. Primer waypoint: {waypoints[0].position}");
        }
        else
        {
            Debug.LogWarning($"Ruta asignada a {gameObject.name} está vacía o es nula.");
        }
    }
}