using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SofaGenerator : MonoBehaviour
{
    public GameObject cubePrefab;

    // Update is called once per frame
    void Update()
    {
        if(Input.GetKeyDown(KeyCode.O)){
            Instantiate(cubePrefab,transform.position,Quaternion.identity);
        }
    }
}
