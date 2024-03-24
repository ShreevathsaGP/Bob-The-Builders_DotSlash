using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BedSpawner : MonoBehaviour
{
    public GameObject cubePrefab;

    // Update is called once per frame
    void Update()
    {
        if(Input.GetKeyDown(KeyCode.B)){
            Instantiate(cubePrefab,transform.position,Quaternion.identity);
        }
    }
}
