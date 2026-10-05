// Automatically use current server, or fallback to localhost:5000 if frontend is hosted separately (e.g. port 8000)
const API_BASE = window.location.port === "5000" ? "" : "http://localhost:5000";
document.getElementById("yr").textContent = new Date().getFullYear();
document.querySelectorAll(".ph img").forEach(i => i.addEventListener("error", () => { i.style.display = "none"; }));

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
async function post(path, data) {
  const url = (API_BASE || "") + path;
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return { ok: r.ok };
}
function wire(id, build, okMsg) {
  const f = document.getElementById(id), s = f.parentElement.querySelector(".status") || f.querySelector(".status");
  f.addEventListener("submit", async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(f));
    const show = (m, ok) => { s.textContent = m; s.className = "status " + (ok ? "ok" : "bad"); };
    if (!EMAIL.test(d.email || "") || (d.name !== undefined && !d.name.trim())) return show("Please enter a valid name and email.", false);
    try { const r = await post(...build(d)); r.ok ? (show(okMsg, true), f.reset()) : show("Something went wrong. Try again.", false); }
    catch { show("Network error. Try again.", false); }
  });
}
// Registration reuses the API's /api/contact endpoint; newsletter uses /api/subscribe.
wire("reg-form", d => ["/api/contact", { name: d.name, email: d.email, body: `Registration for ${d.event}. Phone: ${d.phone || "n/a"}` }], "You're registered. See you there!");
wire("nl-form", d => ["/api/subscribe", { email: d.email }], "Subscribed!");

// Highlight the nav link for the section in view
const links = [...document.querySelectorAll(".nav a")];
["home", "gallery", "register", "contact"].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  new IntersectionObserver(es => es.forEach(e => e.isIntersecting &&
    links.forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + id))), { threshold: .35 }).observe(el);
});
