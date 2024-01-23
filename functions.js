// requests.js

import fs from 'fs/promises';
import fetch from 'node-fetch';

export async function loadImageBase64(imagePath) {
  try {
    const imageBuffer = await fs.readFile(imagePath);
    return imageBuffer.toString('base64');
  } catch (error) {
    throw error;
  }
}

export async function performRequest(url, method, headers, imagePath, latitude, longitude, similarImages, health) {
  try {
    // Load image as base64
    const imageBase64 = await loadImageBase64(imagePath);

    // Build request body
    const bodyData = {
      images: [imageBase64],
      latitude: latitude,
      longitude: longitude,
      similar_images: similarImages,
      health: health
    };

    // Convert request body to JSON string
    const requestBody = JSON.stringify(bodyData);

    // Perform request using fetch
    const response = await fetch(url, {
      method: method,
      headers: headers,
      body: requestBody
    });

    // Process and return the response
    return response.json();
  } catch (error) {
    throw error;
  }
}
