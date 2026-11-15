/** Fire Almanac - roteador (equivalente às rotas de páginas do Flask). */
import { apiFocos } from "./api.js";

// ---------- Base path (GitHub Pages de projeto: usuario.github.io/repo/) ----------
const BASE = location.hostname.endsWith("github.io")
  ? "/" + location.pathname.split("/")[1]
  : "";

// ---------- Rotas de páginas (equivalente aos @app.route) ----------
const ROTAS = {
  "/": "templates/landing.html",      // landing()
  "/mapa": "templates/mapa.html",     // mapa()
};

// ---------- Shim da API: /api/focos continua sendo chamada via fetch ----------
const fetchOriginal = window.fetch.bind(window);

window.fetch = async (url, opcoes = {}) => {
  const caminho = new URL(url, location.href).pathname.replace(BASE, "");
  const metodo = (opcoes.method || "GET").toUpperCase();

  if (caminho === "/api/focos" && metodo === "POST") {
    let payload = {};
    try { payload = JSON.parse(opcoes.body) || {}; } catch { /* silent=True */ }

    const { status, body } = await apiFocos(payload);
    return new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  }
  return fetchOriginal(url, opcoes);
};

// ---------- Utilitários ----------
function caminhoAtual() {
  let p = location.pathname.replace(BASE, "") || "/";
  if (p.length > 1) p = p.replace(/\/+$/, ""); // "/mapa/" -> "/mapa"
  return p;
}

/** Ajusta URLs de assets/links para funcionar com BASE (e relativos à raiz). */
function ajustarUrl(url) {
  if (!url || /^([a-z][a-z0-9+.-]*:|\/\/|#)/i.test(url)) return url;
  return url.startsWith("/") ? BASE + url : `${BASE}/${url}`;
}

function ajustarAtributos(raiz) {
  raiz.querySelectorAll("[href], [src], [action]").forEach((el) => {
    for (const attr of ["href", "src", "action"]) {
      if (el.hasAttribute(attr)) el.setAttribute(attr, ajustarUrl(el.getAttribute(attr)));
    }
  });
}

function carregarCss(href) {
  return new Promise((resolve) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.dataset.pagina = "1";
    link.onload = link.onerror = resolve;
    document.head.appendChild(link);
  });
}

let versao = 0; // força re-execução dos scripts a cada navegação

// ---------- Renderização (equivalente ao render_template) ----------
async function renderizar(caminho) {
  const arquivo = ROTAS[caminho] ?? ROTAS["/"];
  const resp = await fetchOriginal(`${BASE}/${arquivo}`);
  const doc = new DOMParser().parseFromString(await resp.text(), "text/html");
  ajustarAtributos(doc);

  // CSS: remove os da página anterior e carrega os da nova
  document.querySelectorAll("link[data-pagina]").forEach((l) => l.remove());
  const folhas = [...doc.querySelectorAll("link[rel='stylesheet']")];
  await Promise.all(folhas.map((l) => carregarCss(l.getAttribute("href"))));

  // Scripts: separa para recriar (scripts via innerHTML não executam)
  const scripts = [...doc.querySelectorAll("script")];
  scripts.forEach((s) => s.remove());

  // Conteúdo, título e classe do body
  document.title = doc.title || "Fire Almanac";
  document.body.className = doc.body.className;
  document.getElementById("app").innerHTML = doc.body.innerHTML;
  window.scrollTo(0, 0);

  // Executa os scripts da página
  versao++;
  for (const antigo of scripts) {
    const novo = document.createElement("script");
    if (antigo.type) novo.type = antigo.type;
    if (antigo.src) {
      const u = new URL(antigo.getAttribute("src"), location.origin);
      u.searchParams.set("v", versao);
      novo.src = u.pathname + u.search;
    } else {
      novo.textContent = antigo.textContent;
    }
    document.getElementById("app").appendChild(novo);
  }
}

// ---------- Navegação ----------
function navegar(destino) {
  history.pushState({}, "", BASE + destino);
  renderizar(destino);
}

document.addEventListener("click", (e) => {
  const a = e.target.closest("a[href]");
  if (!a || a.target === "_blank" || e.ctrlKey || e.metaKey || e.shiftKey) return;

  const url = new URL(a.href, location.href);
  if (url.origin !== location.origin) return;

  const destino = url.pathname.replace(BASE, "") || "/";
  if (destino in ROTAS) {
    e.preventDefault();
    navegar(destino);
  }
});

window.addEventListener("popstate", () => renderizar(caminhoAtual()));

// ---------- Inicialização (restaura rota vinda do 404.html) ----------
const salva = sessionStorage.getItem("redirect");
if (salva) {
  sessionStorage.removeItem("redirect");
  history.replaceState({}, "", salva);
}
renderizar(caminhoAtual());