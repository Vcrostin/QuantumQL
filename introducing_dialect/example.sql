-- Step 1
PREPARE STATE |db_users>
FROM classical_table user_features
USING amplitude_encoding
ON (age, income, purchase_frequency, avg_basket_value);

-- Step 2
PREPARE STATE |target>
FROM classical_array [0.7, 0.3, 0.9, 0.2]
USING angle_encoding;

-- Step 3
APPLY variational_circuit('feature_map_ansatz_4q')
ON |db_users>
WITH PARAMETERS (0.5, 1.2, 0.8);

-- Step 4
ENTANGLE |db_users> WITH target
AS similarity_link
USING CNOT ON (qubit_1, qubit_1) AND (qubit_2, qubit_2)
      AND (qubit_3, qubit_3) AND (qubit_4, qubit_4);

-- Step 5
AMPLIFY SOURCE |db_users>
WHERE CORRELATION OF similarity_link > 0.9;

-- Step 6
MEASURE |db_users>
INTO classical_output (user_id, distance_score)
WITH CONFIDENCE >= 0.95
SHOTS = 10000;
