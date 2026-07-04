// Solo actualiza el nombre de archivo mostrado en el selector.
// La validación real (columnas, registros, periodo, etc.) ahora la hace
// el backend con Pandas; ver datasets/utils.py::validate_dataset.
(function () {
    const fileInput = document.getElementById('dataset-file');
    const fileNameLabel = document.getElementById('dataset-file-name');

    if (!fileInput || !fileNameLabel) {
        return;
    }

    fileInput.addEventListener('change', function () {
        const file = fileInput.files[0];
        fileNameLabel.textContent = file ? file.name : 'Ningún archivo seleccionado';
    });
})();
