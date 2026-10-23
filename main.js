const PAGE_SIZE = 20;
let rawData = [];
let filterData = [];
let page = 1;

const listEl = document.getElementById("list");
const searchEl = document.getElementById("search");
const totalEl = document.getElementById("total");
const pageEl = document.getElementById("page");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");

async function loadData(){
    const res = await fetch("./data/data.json");
    rawData = await res.json();
    filterData = [...rawData];
    render();
}

function getSeverityClass(s){
    if(s.includes("高危")) return "sev-high";
    if(s.includes("中危")) return "sev-medium";
    return "sev-low";
}

function render(){
    const start = (page -1)*PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const pageItems = filterData.slice(start, end);
    totalEl.textContent = filterData.length;
    pageEl.textContent = page;
    listEl.innerHTML = "";
    pageItems.forEach(it=>{
        const div = document.createElement("div");
        div.className = "item";
        const cls = getSeverityClass(it.severity);
        div.innerHTML = `
            <div class="item-title"><a href="${it.link}" target="_blank">${escapeHtml(it.title)}</a></div>
            <div class="item-meta">
                <span class="item-severity ${cls}">${escapeHtml(it.severity)}</span>
                来源：${escapeHtml(it.source)} | ${escapeHtml(it.time)}
                ${it.cve ? " | CVE："+escapeHtml(it.cve) : ""}
            </div>
            <div class="item-summary">${escapeHtml(it.summary.substring(0,200))}...</div>
        `;
        listEl.appendChild(div);
    })
    prevBtn.disabled = page <= 1;
    nextBtn.disabled = end >= filterData.length;
}

function escapeHtml(s){
    return String(s)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

function doSearch(){
    const kw = searchEl.value.trim().toLowerCase();
    if(!kw){
        filterData = [...rawData];
    }else{
        filterData = rawData.filter(x=>
            x.title.toLowerCase().includes(kw)
            || x.summary.toLowerCase().includes(kw)
            || x.cve.toLowerCase().includes(kw)
            || x.severity.includes(kw)
        )
    }
    page = 1;
    render();
}

searchEl.addEventListener("input", doSearch);
prevBtn.onclick = ()=>{page--;render()};
nextBtn.onclick = ()=>{page++;render()};
loadData();
