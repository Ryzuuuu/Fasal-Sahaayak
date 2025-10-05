// src/api/analysisService.js
import axios from 'axios';

// The URL of your running Python Flask server
const API_URL = 'http://localhost:5000/analyze';

export const getAnalysisReport = async (formData) => {
  console.log("Sending to REAL API:", formData);

  try {
    // Use axios to send a POST request with the form data
    const response = await axios.post(API_URL, formData);
    
    // Log the response from the Python server
    console.log("Received from Python API:", response.data);
    
    // Return the data which will be used to display recommendations
    return response.data;

  } catch (error) {
    // Handle any network errors or errors from the server
    console.error("Error calling the analysis API:", error);
    
    // Throw an error with a user-friendly message
    throw new Error("Could not connect to the analysis server. Please make sure it is running and try again.");
  }
};