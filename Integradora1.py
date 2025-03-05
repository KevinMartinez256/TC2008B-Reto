using UnityEngine;
using System.Collections;
using UnityEngine.Networking;
using System.Collections.Generic;

public class TrafficManager : MonoBehaviour
{
    public GameObject carPrefab;  // Prefab de los autos
    private Dictionary<int, GameObject> cars = new Dictionary<int, GameObject>();

    void Start()
    {
        StartCoroutine(UpdateTraffic());
    }

    IEnumerator UpdateTraffic()
    {
        while (true)
        {
            UnityWebRequest request = UnityWebRequest.Get("http://127.0.0.1:5000/simulate");
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string json = request.downloadHandler.text;
                CarData[] carDataArray = JsonHelper.FromJson<CarData>(json);

                foreach (CarData car in carDataArray)
                {
                    Vector3 newPosition = new Vector3(car.pos[0], 0.13f, car.pos[1]);

                    if (!cars.ContainsKey(car.id))
                    {
                        GameObject newCar = Instantiate(carPrefab, newPosition, Quaternion.identity);
                        cars[car.id] = newCar;
                    }
                    else
                    {
                        // 🔹 Movimiento más suave con Lerp
                        StartCoroutine(MoveCarSmoothly(cars[car.id], newPosition));
                    }
                }
            }
            yield return new WaitForSeconds(1); // Actualizar cada segundo
        }
    }

    IEnumerator MoveCarSmoothly(GameObject car, Vector3 targetPosition)
    {
        float duration = 0.5f; // Tiempo para la transición
        float elapsedTime = 0;
        Vector3 startPosition = car.transform.position;

        while (elapsedTime < duration)
        {
            car.transform.position = Vector3.Lerp(startPosition, targetPosition, (elapsedTime / duration));
            elapsedTime += Time.deltaTime;
            yield return null;
        }
        car.transform.position = targetPosition;
    }

    [System.Serializable]
    public class CarData
    {
        public int id;
        public int[] pos;
    }

    public static class JsonHelper
    {
        public static T[] FromJson<T>(string json)
        {
            string newJson = "{\"array\":" + json + "}";
            Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);
            return wrapper.array;
        }

        [System.Serializable]
        private class Wrapper<T>
        {
            public T[] array;
        }
    }
}
