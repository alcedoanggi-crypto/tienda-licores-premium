const PALETA_ADMIN = {
  ambar: "#B8860B",
  dorado: "#D4AF37",
  doradoClaro: "#E8C766",
  hueso: "#F5F1E8",
};

const SERIE_ADMIN = [PALETA_ADMIN.ambar, PALETA_ADMIN.dorado, "#8a6a1f", PALETA_ADMIN.doradoClaro, "#6b5416", "#a67c2e", "#c9a04a", "#5c4712"];

async function obtenerJSON(url) {
  const respuesta = await fetch(url);
  return respuesta.json();
}

function opcionesOscuras(indexAxis) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: indexAxis || "x",
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, grid: { color: "rgba(212,175,55,0.08)" }, ticks: { color: "#857f70" } },
      x: { grid: { display: false }, ticks: { color: "#857f70" } },
    },
  };
}

document.addEventListener("DOMContentLoaded", async () => {
  const masVendidos = await obtenerJSON("/admin/api/productos-mas-vendidos");
  new Chart(document.getElementById("graficoMasVendidos"), {
    type: "bar",
    data: { labels: masVendidos.labels, datasets: [{ data: masVendidos.valores, backgroundColor: PALETA_ADMIN.dorado, borderRadius: 4 }] },
    options: opcionesOscuras(),
  });

  const categorias = await obtenerJSON("/admin/api/ventas-por-categoria");
  new Chart(document.getElementById("graficoCategorias"), {
    type: "doughnut",
    data: { labels: categorias.labels, datasets: [{ data: categorias.valores, backgroundColor: SERIE_ADMIN, borderWidth: 1, borderColor: "#1c1a17" }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { color: "#c9c3b6", boxWidth: 12, font: { size: 11 } } } },
    },
  });

  const ingresos = await obtenerJSON("/admin/api/ingresos-mensuales");
  new Chart(document.getElementById("graficoIngresos"), {
    type: "line",
    data: {
      labels: ingresos.labels,
      datasets: [{
        data: ingresos.valores,
        borderColor: PALETA_ADMIN.dorado,
        backgroundColor: "rgba(212,175,55,0.15)",
        fill: true,
        tension: 0.35,
        pointBackgroundColor: PALETA_ADMIN.dorado,
      }],
    },
    options: opcionesOscuras(),
  });
});
