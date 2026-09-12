const navLinks = document.querySelectorAll('.nav-link');
const searchInput = document.getElementById('searchInput');
const scanRows = document.querySelectorAll('.scan-item');
const scanButton = document.getElementById('scanButton');
const modal = document.getElementById('scanModal');
const closeModalBtn = document.querySelector('.close-btn');
const modalBackdrop = document.querySelector('.modal-backdrop');

navLinks.forEach((link) => {
  link.addEventListener('click', () => {
    navLinks.forEach((item) => item.classList.remove('active'));
    link.classList.add('active');
  });
});

searchInput.addEventListener('input', () => {
  const term = searchInput.value.trim().toLowerCase();

  scanRows.forEach((row) => {
    const text = row.dataset.product.toLowerCase();
    row.style.display = text.includes(term) || term === '' ? 'grid' : 'none';
  });
});

const openModal = () => {
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
};

const closeModal = () => {
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
};

scanButton.addEventListener('click', openModal);
closeModalBtn.addEventListener('click', closeModal);
modalBackdrop.addEventListener('click', closeModal);

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
    closeModal();
  }
});

const chartSvg = document.querySelector('.chart-svg');
const chartValues = [52, 58, 63, 71, 78, 89, 93];

const buildChart = () => {
  const width = 420;
  const height = 170;
  const padding = { top: 18, right: 18, bottom: 24, left: 18 };

  const max = 100;
  const min = 40;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const points = chartValues.map((value, index) => {
    const x = padding.left + (index / (chartValues.length - 1)) * chartWidth;
    const y = padding.top + ((max - value) / (max - min)) * chartHeight;
    return { x, y };
  });

  const linePath = points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ');

  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - padding.bottom} L ${points[0].x} ${height - padding.bottom} Z`;

  const lines = Array.from({ length: 4 }, (_, index) => {
    const y = padding.top + (index * chartHeight) / 3;
    return `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" />`;
  }).join('');

  chartSvg.innerHTML = `
    <defs>
      <linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="#8dbb9e" stop-opacity="0.38" />
        <stop offset="100%" stop-color="#8dbb9e" stop-opacity="0.08" />
      </linearGradient>
    </defs>
    ${lines}
    <path class="chart-area" d="${areaPath}"></path>
    <path class="chart-line" d="${linePath}"></path>
  `;
};

buildChart();
window.addEventListener('resize', buildChart);
