// Simulación visual del entrenamiento del modelo (sin scikit-learn, sin entrenamiento real).
// Solo actualiza el modal y las cards de la página con datos de demostración.
(function () {
    const trainBtn = document.getElementById('train-model-btn');
    const modal = document.getElementById('training-modal');
    const modalSymbol = document.getElementById('training-modal-symbol');
    const modalIcon = document.getElementById('training-modal-icon');
    const modalTitle = document.getElementById('training-modal-title');
    const modalText = document.getElementById('training-modal-text');
    const modalClose = document.getElementById('training-modal-close');
    const kpiStatus = document.getElementById('kpi-model-status');
    const kpiLastTrained = document.getElementById('kpi-last-trained');

    if (!trainBtn || !modal) {
        return;
    }

    function formatNow() {
        const now = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        return `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
    }

    function showTrainingState() {
        modal.classList.remove('hidden');
        modalSymbol.textContent = 'progress_activity';
        modalSymbol.classList.add('animate-spin');
        modalIcon.classList.remove('bg-green-100', 'text-green-700');
        modalIcon.classList.add('bg-orange-50', 'text-primary');
        modalTitle.textContent = 'Entrenando modelo...';
        modalText.textContent = 'Procesando el dataset histórico y ajustando variables.';
        modalClose.classList.add('hidden');
        trainBtn.disabled = true;
    }

    function showSuccessState() {
        modalSymbol.classList.remove('animate-spin');
        modalSymbol.textContent = 'check_circle';
        modalIcon.classList.remove('bg-orange-50', 'text-primary');
        modalIcon.classList.add('bg-green-100', 'text-green-700');
        modalTitle.textContent = 'Modelo entrenado exitosamente';
        modalText.textContent = 'Random Forest sigue siendo el mejor modelo (R² 0.87). Métricas de demostración.';
        modalClose.classList.remove('hidden');
        trainBtn.disabled = false;

        if (kpiStatus) kpiStatus.textContent = 'Entrenado';
        if (kpiLastTrained) kpiLastTrained.textContent = formatNow();
    }

    trainBtn.addEventListener('click', function () {
        showTrainingState();
        window.setTimeout(showSuccessState, 1800);
    });

    modalClose.addEventListener('click', function () {
        modal.classList.add('hidden');
    });
})();
