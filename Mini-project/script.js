const API_BASE = 'http://127.0.0.1:8000/api';

const trainBtn = document.getElementById('trainBtn');
const stepBtn = document.getElementById('stepBtn');
const autoPlayBtn = document.getElementById('autoPlayBtn');
const statusText = document.getElementById('statusText');
const agentStatusLabel = document.getElementById('agentStatusLabel');

const hourVal = document.getElementById('hourVal');
const socVal = document.getElementById('socVal');
const tariffVal = document.getElementById('tariffVal');
const actionVal = document.getElementById('actionVal');
const logList = document.getElementById('logList');
const totalSavingsEl = document.getElementById('totalSavings');

let totalSavings = 0.0;
let isAutoPlaying = false;
let autoPlayInterval;

const ctx = document.getElementById('bessChart').getContext('2d');

// ОНОВЛЕНИЙ ГРАФІК (Комбінований)
const chartData = {
    labels: [],
    datasets: [
        {
            type: 'bar',
            label: 'Дія (⬆ Заряд / ⬇ Розряд)',
            data: [],
            backgroundColor: [], // Кольори будуть додаватись динамічно
            borderRadius: 4,
            yAxisID: 'y_action',
            order: 3
        },
        {
            type: 'line',
            label: 'Рівень заряду (SOC)',
            data: [],
            borderColor: '#9b51e0',
            backgroundColor: 'rgba(155, 81, 224, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            yAxisID: 'y_soc',
            order: 2
        },
        {
            type: 'line',
            label: 'Тариф (Ціна)',
            data: [],
            borderColor: '#8a859b',
            borderDash: [5, 5],
            borderWidth: 2,
            fill: false,
            tension: 0.1,
            yAxisID: 'y_tariff',
            order: 1
        }
    ]
};

const bessChart = new Chart(ctx, {
    data: chartData,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' } },
            y_soc: {
                type: 'linear', display: true, position: 'left',
                title: { display: true, text: 'SOC (кВт)' },
                min: 0, max: 12,
                grid: { color: 'rgba(255,255,255,0.05)' }
            },
            y_tariff: {
                type: 'linear', display: true, position: 'right',
                title: { display: true, text: 'Тариф (₴)' },
                min: 0, max: 6,
                grid: { drawOnChartArea: false }
            },
            y_action: {
                type: 'linear', display: false, // Ховаємо саму вісь, але використовуємо її масштаб
                min: -2, max: 2
            }
        },
        plugins: {
            legend: { labels: { color: '#fff' } }
        }
    }
});

trainBtn.addEventListener('click', async () => {
    try {
        trainBtn.disabled = true;
        statusText.innerText = 'Навчання... Це займе 2-3 секунди';

        const response = await fetch(`${API_BASE}/train?episodes=2000`, { method: 'POST' });
        if (!response.ok) throw new Error('API Error');
        const data = await response.json();

        statusText.innerText = `Навчено успішно! (Епізодів: ${data.episodes})`;
        agentStatusLabel.innerText = 'Online';
        agentStatusLabel.className = 'online';

        stepBtn.disabled = false;
        autoPlayBtn.disabled = false;
        trainBtn.innerText = 'Перенавчити';
        trainBtn.disabled = false;
    } catch (error) {
        statusText.innerText = 'Помилка API';
        trainBtn.disabled = false;
    }
});

async function makeStep() {
    try {
        const response = await fetch(`${API_BASE}/step`);
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error(error);
    }
}

stepBtn.addEventListener('click', makeStep);

autoPlayBtn.addEventListener('click', () => {
    isAutoPlaying = !isAutoPlaying;
    if (isAutoPlaying) {
        autoPlayBtn.innerText = 'Зупинити';
        autoPlayBtn.classList.add('btn-primary');
        stepBtn.disabled = true;
        autoPlayInterval = setInterval(makeStep, 800); // Трохи пришвидшили анімацію
    } else {
        autoPlayBtn.innerText = 'Авто-симуляція';
        autoPlayBtn.classList.remove('btn-primary');
        stepBtn.disabled = false;
        clearInterval(autoPlayInterval);
    }
});

function updateUI(data) {
    hourVal.innerText = `${data.hour.toString().padStart(2, '0')}:00`;
    socVal.innerText = `${data.soc.toFixed(1)} кВт`;
    tariffVal.innerText = `${data.tariff.toFixed(1)} ₴`;
    actionVal.innerText = data.action;

    let actionColor = 'var(--text-main)';
    let logClass = 'log-hold';
    let barValue = 0;
    let barColor = 'transparent';

    if (data.action === 'Charge') {
        actionColor = 'var(--action-charge)';
        logClass = 'log-charge';
        barValue = 1; // Стовпчик вгору
        barColor = 'rgba(74, 222, 128, 0.8)'; // Зелений
    }
    else if (data.action === 'Discharge') {
        actionColor = 'var(--action-discharge)';
        logClass = 'log-discharge';
        barValue = -1; // Стовпчик вниз
        barColor = 'rgba(248, 113, 113, 0.8)'; // Червоний
    }

    actionVal.style.color = actionColor;

    totalSavings += data.savings;
    totalSavingsEl.innerText = `Економія: ${totalSavings.toFixed(2)} ₴`;

    const timeLabel = `${data.hour.toString().padStart(2, '0')}:00`;
    chartData.labels.push(timeLabel);
    chartData.datasets[0].data.push(barValue); // Дія (стовпчик)
    chartData.datasets[0].backgroundColor.push(barColor);
    chartData.datasets[1].data.push(data.soc); // SOC (лінія)
    chartData.datasets[2].data.push(data.tariff); // Тариф (лінія)

    if (chartData.labels.length > 24) {
        chartData.labels.shift();
        chartData.datasets[0].data.shift();
        chartData.datasets[0].backgroundColor.shift();
        chartData.datasets[1].data.shift();
        chartData.datasets[2].data.shift();
    }
    bessChart.update();

    const li = document.createElement('li');
    li.className = `log-item ${logClass}`;
    li.innerHTML = `
        <span>Час: ${timeLabel} | Дія: <strong>${data.action}</strong></span>
        <span>${data.savings > 0 ? '+ ' + data.savings.toFixed(2) + ' ₴ економії' : ''}</span>
    `;
    logList.prepend(li);

    if (logList.children.length > 10) logList.removeChild(logList.lastChild);
}