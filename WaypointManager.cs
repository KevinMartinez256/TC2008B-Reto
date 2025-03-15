using UnityEngine;
using System.Collections.Generic;

public class WaypointManager : MonoBehaviour
{
    public List<Transform> waypoints; // Lista de waypoints en la escena

    void Awake()
    {
        waypoints = new List<Transform>(); // Inicializar la lista de waypoints

        // Buscar waypoints entre los hijos directos del objeto
        foreach (Transform child in transform)
        {
            if (child.name.ToLower().StartsWith("waypoint")) // Si el nombre comienza con "waypoint"
            {
                waypoints.Add(child); // Añadir a la lista
                Debug.Log($"Waypoint {child.name} encontrado en {child.position} (índice: {waypoints.Count - 1})");
            }
            else
            {
                Debug.Log($"Objeto {child.name} no es un waypoint (no comienza con 'Waypoint').");
            }
        }

        // Si no se encontraron waypoints como hijos, buscar por tag en toda la escena
        if (waypoints.Count == 0)
        {
            Debug.Log("No se encontraron waypoints como hijos directos. Buscando en toda la escena...");
            GameObject[] waypointObjects = GameObject.FindGameObjectsWithTag("Waypoint");
            foreach (GameObject waypointObj in waypointObjects)
            {
                waypoints.Add(waypointObj.transform);
                Debug.Log($"Waypoint {waypointObj.name} encontrado en {waypointObj.transform.position} (índice: {waypoints.Count - 1}, buscado por tag 'Waypoint')");
            }
        }

        // Mostrar información sobre los waypoints encontrados
        Debug.Log($"Total de waypoints encontrados: {waypoints.Count}");
        if (waypoints.Count > 0)
        {
            Debug.Log($"Primer waypoint encontrado en {waypoints[0].position}. Total de waypoints: {waypoints.Count}.");
        }
        else
        {
            Debug.LogError("🚨 No se detectaron waypoints. Asegúrate de que los waypoints existan y tengan el tag 'Waypoint'.");
        }
    }
}