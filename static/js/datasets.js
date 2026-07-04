// Validación de demostración para la carga del Dataset Histórico.
// Solo revisa la extensión del archivo en el navegador; no lee ni procesa
// su contenido. La lectura real (pandas) se conectará después en el backend.
(function () {
    const fileInput = document.getElementById('dataset-file');
    const fileNameLabel = document.getElementById('dataset-file-name');
    const uploadBtn = document.getElementById('dataset-upload-btn');
    const messageBox = document.getElementById('dataset-upload-message');

    if (!fileInput || !uploadBtn || !messageBox) {
        return;
    }

    const ALLOWED_EXTENSIONS = ['csv', 'xlsx'];

    function showMessage(text, isSuccess) {
        messageBox.textContent = text;
        messageBox.classList.remove('hidden', 'upload-message--success', 'upload-message--error');
        messageBox.classList.add(isSuccess ? 'upload-message--success' : 'upload-message--error');
    }

    fileInput.addEventListener('change', function () {
        const file = fileInput.files[0];
        fileNameLabel.textContent = file ? file.name : 'Ningún archivo seleccionado';
    });

    uploadBtn.addEventListener('click', function () {
        const file = fileInput.files[0];

        if (!file) {
            showMessage('Selecciona un archivo .csv o .xlsx antes de continuar.', false);
            return;
        }

        const extension = file.name.split('.').pop().toLowerCase();

        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            showMessage('Formato no soportado. Usa un archivo .csv o .xlsx.', false);
            return;
        }

        showMessage(
            'Archivo "' + file.name + '" cargado correctamente (modo demostración). ' +
            'Todavía no se procesa en el servidor.',
            true
        );
    });
})();
