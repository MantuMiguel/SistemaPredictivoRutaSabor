// Habilita "Tipo de promoción" y "Descuento (%)" solo cuando el usuario
// marca "Sí" en "Promoción planificada". No hace ninguna predicción en el
// navegador: solo ordena el formulario antes de enviarlo al servidor.
(function () {
    const promocion = document.getElementById('promocion-activa');
    const tipo = document.getElementById('tipo-promocion');
    const descuento = document.getElementById('descuento-pct');

    if (!promocion || !tipo || !descuento) {
        return;
    }

    function actualizar() {
        const activa = promocion.value === 'Sí';
        tipo.disabled = !activa;
        descuento.disabled = !activa;
        [tipo, descuento].forEach(function (campo) {
            campo.classList.toggle('bg-gray-50', !activa);
            campo.classList.toggle('text-gray-400', !activa);
            campo.classList.toggle('text-gray-700', activa);
        });
        if (!activa) {
            tipo.value = 'Ninguna';
            descuento.value = '0';
        }
    }

    promocion.addEventListener('change', actualizar);
    actualizar();
})();
