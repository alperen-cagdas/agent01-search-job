async function loadJson(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

function formatDate(iso) {
  if (!iso) return "Henüz çalıştırılmadı";
  try {
    return new Date(iso).toLocaleString("tr-TR", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function sourceLabel(source) {
  return source === "kariyer.net" ? "kariyer.net" : source === "indeed" ? "Indeed" : source;
}

function renderStatusBanner(sourcesStatus) {
  const banner = document.getElementById("status-banner");
  const failed = Object.entries(sourcesStatus || {})
    .filter(([, status]) => status === "failed")
    .map(([name]) => sourceLabel(name));

  if (failed.length === 0) {
    banner.hidden = true;
    return;
  }
  banner.hidden = false;
  banner.textContent = `${failed.join(", ")} bugün için veri döndürmedi — sonuçlar diğer kaynaktan / son başarılı güncellemeden gösteriliyor.`;
}

function renderJobs(jobs) {
  const container = document.getElementById("jobs-container");
  container.innerHTML = "";

  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<p class="empty-state">Bugün için eşleşen ilan bulunamadı.</p>';
    return;
  }

  const grouped = {};
  for (const job of jobs) {
    grouped[job.source] = grouped[job.source] || [];
    grouped[job.source].push(job);
  }

  for (const [source, sourceJobs] of Object.entries(grouped)) {
    const group = document.createElement("div");
    group.className = "source-group";

    const heading = document.createElement("h3");
    heading.textContent = `${sourceLabel(source)} (${sourceJobs.length})`;
    group.appendChild(heading);

    for (const job of sourceJobs) {
      group.appendChild(renderJobCard(job));
    }
    container.appendChild(group);
  }
}

function renderJobCard(job) {
  const card = document.createElement("div");
  card.className = "job-card";

  const title = document.createElement("a");
  title.className = "job-title";
  title.href = job.url;
  title.target = "_blank";
  title.rel = "noopener noreferrer";
  title.textContent = job.title;
  card.appendChild(title);

  const meta = document.createElement("p");
  meta.className = "job-meta";
  meta.innerHTML = `${job.company} &middot; ${job.location} &middot; <span class="job-score">Puan: ${job.score}</span>${job.posted_date ? " &middot; " + job.posted_date : ""}`;
  card.appendChild(meta);

  if (job.description_snippet) {
    const snippet = document.createElement("p");
    snippet.className = "job-snippet";
    snippet.textContent = job.description_snippet;
    card.appendChild(snippet);
  }

  if (job.matched_keywords && job.matched_keywords.length > 0) {
    const tags = document.createElement("div");
    tags.className = "keyword-tags";
    for (const kw of job.matched_keywords) {
      const tag = document.createElement("span");
      tag.className = "keyword-tag";
      tag.textContent = kw;
      tags.appendChild(tag);
    }
    card.appendChild(tags);
  }

  return card;
}

function renderCompanies(data) {
  const container = document.getElementById("companies-container");
  const list = document.createElement("ul");
  list.className = "company-list";

  for (const company of data.companies || []) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = company.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = company.name;
    li.appendChild(a);
    if (company.note) {
      const note = document.createElement("span");
      note.className = "company-note";
      note.textContent = company.note;
      li.appendChild(note);
    }
    list.appendChild(li);
  }
  container.appendChild(list);
}

function renderLinkedInLinks(data) {
  const container = document.getElementById("linkedin-container");
  const list = document.createElement("ul");
  list.className = "linkedin-list";

  for (const link of data.links || []) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = link.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = link.label;
    li.appendChild(a);
    list.appendChild(li);
  }
  container.appendChild(list);
}

async function main() {
  try {
    const latest = await loadJson("data/latest.json");
    document.getElementById("last-updated").textContent = `Son güncelleme: ${formatDate(latest.generated_at)}`;
    renderStatusBanner(latest.sources_status);
    renderJobs(latest.jobs);
  } catch (e) {
    document.getElementById("jobs-container").innerHTML =
      '<p class="empty-state">İlan verisi yüklenemedi.</p>';
    console.error(e);
  }

  try {
    const companies = await loadJson("data/companies.json");
    renderCompanies(companies);
  } catch (e) {
    document.getElementById("companies-container").innerHTML =
      '<p class="empty-state">Firma listesi yüklenemedi.</p>';
    console.error(e);
  }

  try {
    const linkedin = await loadJson("data/linkedin_links.json");
    renderLinkedInLinks(linkedin);
  } catch (e) {
    document.getElementById("linkedin-container").innerHTML =
      '<p class="empty-state">LinkedIn link listesi yüklenemedi.</p>';
    console.error(e);
  }
}

main();
