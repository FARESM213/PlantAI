import { performRequest } from './requests';

// Example of using the function
const urlExample = 'https://plant.id/api/v3/identification';
const methodExample = 'POST';
const headersExample = {
    'Api-Key': 'f9hqDGhZLxY48orHhoGZWRqmOvMZYGTp6uMh0SSDqs1wGmQmep',
    'Content-Type': 'application/json'
};
const imagePathExample = 'tomate-mildiou-maladie.jpg';
const latitudeExample = 48.866; //Paris
const longitudeExample = 2.333; //Paris
const similarImagesExample = true;
const healthExample = 'all';

// Call the function to perform the request with the JSON file content
performRequest(urlExample, methodExample, headersExample, imagePathExample, latitudeExample, longitudeExample, similarImagesExample, healthExample)
    .then(data => {
        console.log('Server Response:', data);
    })
    .catch(error => {
        console.error('Error during the request:', error);
    });
