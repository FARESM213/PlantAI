function previewFile() {
    var preview = document.getElementById('image-preview');
    var file = document.getElementById('file-upload').files[0];
    var reader = new FileReader();

    reader.onloadend = function () {
        preview.src = reader.result;
        preview.style.display = 'block';
    };

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = "";
        preview.style.display = 'none';
    }
}
// Fonction pour formater la classe prédite
function formatPredictedClass(predictedClass) {
    // Remplacez chaque '_' par un espace
    var formattedClass = predictedClass.replace(/_/g, ' ');
    
    // Supprimez les espaces consécutifs en les remplaçant par un seul espace
    formattedClass = formattedClass.replace(/\s+/g, ' ');
    
    return formattedClass;
}

function sendData(input) {
    var form = new FormData();

    if (input instanceof Blob) {
        form.append('file', input);
    } else {
        form.append('file', input);
    }

    fetch('/predict/', {
        method: 'POST',
        body: form
    })
    .then(response => response.json()) // S'assurer que la réponse est traitée en tant que JSON
    .then(data => {
        var responseContainer = document.getElementById('response');
        responseContainer.innerHTML = ''; // Effacer l'ancienne réponse

        // Formatez la classe prédite
        var formattedPredictedClass = formatPredictedClass(data.predicted_class);

        // Crypter la valeur formatée avant de l'ajouter à l'URL 
        var encryptedValue = encrypt(formattedPredictedClass);
        document.getElementById("chat-link").href = `/chat?predictedClass=${encryptedValue}`;

        var htmlContent = '<h2>Résultats de Prédiction</h2>';
        htmlContent += '<p><strong>Classe prédite :</strong> ' + formattedPredictedClass + '</p>';
        htmlContent += '<h3>Top 3 des prédictions :</h3><ul>';

        for (var key in data.top_3_predictions) {
            htmlContent += '<li> ' + formatPredictedClass(key) + ': ' + (data.top_3_predictions[key] * 100).toFixed(2) + '%</li>';
        }

        htmlContent += '</ul>';
        responseContainer.innerHTML = htmlContent;
        document.getElementById('questions').style.display = 'block';

    })
    .catch(error => {
        console.error('Erreur lors de la récupération des données: ', error);
    });
}

function predictDisease() {
    var fileInput = document.getElementById('file-upload').files[0];
    if (fileInput) {
        sendData(fileInput);
    } else {
        alert("Veuillez télécharger une image.");
    }
}


function encrypt(text) {
    var result = "";
    for (var i = 0; i < text.length; i++) {
        var charCode = text.charCodeAt(i);
        result += String.fromCharCode(charCode + 1); 
    }
    return result;
}