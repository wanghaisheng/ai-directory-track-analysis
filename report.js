// 简单报表JS，依赖PapaParse和ECharts
const resultsDir = 'results/';
const today = new Date().toISOString().slice(0, 10);
let allFiles = [];
let domains = [];
let dates = new Set();

function fetchFileList() {
  // 由于浏览器安全限制，前端无法直接列目录，需后端或手动维护文件列表，或用静态文件清单
  // 这里假设已手动维护文件名列表
  allFiles = [
    // 这里请用实际文件名列表替换，或用后端API动态获取
    // 示例：'aiagentslive_com_lastpart_2025-05-30.csv', ...
  ];
  // 自动提取域名和日期
  const domainSet = new Set();
  allFiles.forEach(f => {
    const m = f.match(/^(.+?)_all\.csv$/);
    if (m) domainSet.add(m[1]);
    const d = f.match(/_(\d{4}-\d{2}-\d{2})\.csv$/);
    if (d) dates.add(d[1]);
  });
  domains = Array.from(domainSet);
  dates = Array.from(dates).sort().reverse();
}

function fillSelectors() {
  const domainSel = document.getElementById('domainSelect');
  const dateSel = document.getElementById('dateSelect');
  domainSel.innerHTML = domains.map(d => `<option value="${d}">${d}</option>`).join('');
  dateSel.innerHTML = dates.map(d => `<option value="${d}">${d}</option>`).join('');
}

function loadReport() {
  const domain = document.getElementById('domainSelect').value;
  const date = document.getElementById('dateSelect').value;
  loadTable(`${resultsDir}${domain}_all.csv`, 'allUrlTable');
  loadTable(`${resultsDir}${domain}_new_${date}.csv`, 'newUrlTable');
  loadPieChart(date);
}

function loadTable(csvPath, tableId) {
  Papa.parse(csvPath, {
    download: true,
    complete: function(results) {
      const tbody = document.getElementById(tableId).querySelector('tbody');
      tbody.innerHTML = '';
      results.data.forEach(row => {
        if (row[0]) {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${row[0]}</td>`;
          tbody.appendChild(tr);
        }
      });
    }
  });
}

function loadPieChart(date) {
  // 合并所有 *_lastpart_date.csv 文件
  const lastpartFiles = allFiles.filter(f => f.endsWith(`lastpart_${date}.csv`));
  let allParts = [];
  let loaded = 0;
  if (lastpartFiles.length === 0) {
    renderPie([]);
    return;
  }
  lastpartFiles.forEach(f => {
    Papa.parse(resultsDir + f, {
      download: true,
      complete: function(results) {
        allParts = allParts.concat(results.data.map(r => r[0]).filter(Boolean));
        loaded++;
        if (loaded === lastpartFiles.length) {
          // 统计词频
          const freq = {};
          allParts.forEach(x => { freq[x] = (freq[x] || 0) + 1; });
          // 取前20高频
          const sorted = Object.entries(freq).sort((a,b) => b[1]-a[1]).slice(0,20);
          renderPie(sorted);
        }
      }
    });
  });
}

function renderPie(data) {
  const chartDom = document.getElementById('pieChart');
  const myChart = echarts.init(chartDom);
  const option = {
    title: { text: 'lastpart词频Top20', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      name: '词频',
      type: 'pie',
      radius: '60%',
      data: data.map(([name, value]) => ({ name, value })),
      label: { formatter: '{b}: {c} ({d}%)' }
    }]
  };
  myChart.setOption(option);
}

window.onload = function() {
  fetchFileList();
  fillSelectors();
  if (domains.length && dates.length) loadReport();
};