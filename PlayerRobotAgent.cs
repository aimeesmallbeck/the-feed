using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Sensors;
using Unity.MLAgents.Actuators;

public class PlayerRobotAgent : Agent
{
    [Header("Movement Settings")]
    public float moveSpeed = 5f;
    public float rotationSpeed = 180f;
    public float jumpForce = 5f;
    
    [Header("Rewards")]
    public float starCollectReward = 1.0f;
    public float timePenalty = -0.001f;
    public float fallPenalty = -1.0f;
    
    private Rigidbody rb;
    private Vector3 startingPosition;
    private int starsCollected = 0;
    private bool isGrounded = true;
    
    public override void Initialize()
    {
        rb = GetComponent<Rigidbody>();
        startingPosition = transform.position;
    }
    
    public override void OnEpisodeBegin()
    {
        // Reset position
        transform.position = startingPosition;
        transform.rotation = Quaternion.identity;
        rb.linearVelocity = Vector3.zero;
        rb.angularVelocity = Vector3.zero;
        
        // Reset stars
        starsCollected = 0;
        
        // Re-enable all stars
        GameObject[] stars = GameObject.FindGameObjectsWithTag("Star");
        foreach (GameObject star in stars)
        {
            star.SetActive(true);
        }
    }
    
    public override void CollectObservations(VectorSensor sensor)
    {
        // Agent's position and velocity
        sensor.AddObservation(transform.position);
        sensor.AddObservation(rb.linearVelocity);
        
        // Agent's rotation (forward direction)
        sensor.AddObservation(transform.forward);
        
        // Find nearest star
        GameObject[] stars = GameObject.FindGameObjectsWithTag("Star");
        Vector3 nearestStarPos = Vector3.zero;
        float nearestDistance = float.MaxValue;
        
        foreach (GameObject star in stars)
        {
            if (star.activeSelf)
            {
                float dist = Vector3.Distance(transform.position, star.transform.position);
                if (dist < nearestDistance)
                {
                    nearestDistance = dist;
                    nearestStarPos = star.transform.position;
                }
            }
        }
        
        // Add nearest star position and distance
        sensor.AddObservation(nearestStarPos);
        sensor.AddObservation(nearestDistance);
        
        // Raycast sensors for obstacles (simplified)
        RaycastHit hit;
        float rayDistance = 5f;
        
        // Forward ray
        if (Physics.Raycast(transform.position, transform.forward, out hit, rayDistance))
        {
            sensor.AddObservation(hit.distance / rayDistance);
        }
        else
        {
            sensor.AddObservation(1f);
        }
        
        // Is grounded
        sensor.AddObservation(isGrounded ? 1f : 0f);
    }
    
    public override void OnActionReceived(ActionBuffers actions)
    {
        // Continuous actions: move forward/backward, rotate left/right
        float move = actions.ContinuousActions[0];
        float rotate = actions.ContinuousActions[1];
        
        // Move
        Vector3 moveDirection = transform.forward * move * moveSpeed;
        rb.linearVelocity = new Vector3(moveDirection.x, rb.linearVelocity.y, moveDirection.z);
        
        // Rotate
        transform.Rotate(0f, rotate * rotationSpeed * Time.fixedDeltaTime, 0f);
        
        // Discrete action: jump (action index 0) - DISABLED FOR DEBUGGING
        // if (actions.DiscreteActions[0] == 1 && isGrounded)
        // {
        //     rb.AddForce(Vector3.up * jumpForce, ForceMode.Impulse);
        //     isGrounded = false;
        // }
        
        // Time penalty to encourage efficiency
        AddReward(timePenalty);
        
        // Check if fell off the platform
        if (transform.position.y < -5f)
        {
            AddReward(fallPenalty);
            EndEpisode();
        }
    }
    
    public override void Heuristic(in ActionBuffers actionsOut)
    {
        // Manual control for testing - movement only, no jump for now
        var continuousActions = actionsOut.ContinuousActions;
        continuousActions[0] = Input.GetAxis("Vertical");   // W/S
        continuousActions[1] = Input.GetAxis("Horizontal"); // A/D
        
        var discreteActions = actionsOut.DiscreteActions;
        discreteActions[0] = 0; // Disable jump in manual mode
        
        // Debug: Confirm this version is running
        Debug.Log("VERSION 2 - Jump code commented out - No jump should occur");
    }
    
    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Star"))
        {
            // Collected a star!
            other.gameObject.SetActive(false);
            starsCollected++;
            AddReward(starCollectReward);
            
            // Check if all stars collected
            GameObject[] remainingStars = GameObject.FindGameObjectsWithTag("Star");
            bool anyActive = false;
            foreach (GameObject star in remainingStars)
            {
                if (star.activeSelf) anyActive = true;
            }
            
            if (!anyActive)
            {
                // All stars collected - episode complete!
                EndEpisode();
            }
        }
    }
    
    private void OnCollisionEnter(Collision collision)
    {
        // Check if grounded
        if (collision.contacts[0].normal.y > 0.5f)
        {
            isGrounded = true;
        }
    }
}
