// Lokalnie: http://127.0.0.1:8000
const API = localStorage.getItem("apiUrl") || window.API_URL || "http://127.0.0.1:8000";

async function fillVoivodeships() {
  const sel = document.getElementById("voi");
  const unit = document.getElementById("unit");
  try {
    const data = await api("/units");
    window._voi = data.voivodeships || [];
    if (sel) {
      data.voivodeships.forEach((v) => {
        const o = document.createElement("option");
        o.value = v.id;
        o.textContent = v.label;
        sel.appendChild(o);
      });
    }
    if (unit) {
      (data.login_units || []).forEach((u) => {
        const o = document.createElement("option");
        o.value = u.code;
        o.textContent = u.code + " — " + u.name;
        unit.appendChild(o);
      });
    }
  } catch (e) {}
}
document.addEventListener("DOMContentLoaded", function () {
  fillVoivodeships();
  renderSession();
  applyOfficerGate();
  if (localStorage.getItem("citizenToken") && document.getElementById("citizenAppView")) {
    loadCitizenDashboard();
  }
});

function renderSession() {
  const el = document.getElementById("session");
  if (!el) return;
  const unit = localStorage.getItem("officerUnitName") || localStorage.getItem("officerUnit");
  const off = localStorage.getItem("officerToken");
  const cit = localStorage.getItem("citizenToken");
  const who = localStorage.getItem("citizenPhone");
  if (cit) {
    el.innerHTML = '<span>Obywatel: <strong>' + (who || "profil") + '</strong></span> <button type="button" class="linkish" onclick="logoutOfficer()">Wyloguj</button>';
    return;
  }
  if (!off) {
    el.innerHTML = '<span class="muted">Niezalogowany</span><button type="button" class="linkish" onclick="logoutOfficer()">Wyloguj</button>';
    return;
  }
  el.innerHTML = '<span>Zalogowano: <strong>' + (unit || "służba") + '</strong></span> <button type="button" class="linkish" onclick="logoutOfficer()">Wyloguj</button>';
}
function setNavVisible(on) {
  const nav = document.getElementById("appNav");
  const session = document.getElementById("session");
  if (nav) nav.style.display = on ? "flex" : "none";
  if (session) session.style.display = on ? "flex" : "none";
}

function applyOfficerGate() {
  const login = document.getElementById("officerLoginView");
  const app = document.getElementById("officerAppView");
  const on = !!localStorage.getItem("officerToken");
  if (login || app) setNavVisible(on);
  if (login) login.style.display = on ? "none" : "block";
  if (app) app.style.display = on ? "block" : "none";
  if (!on) {
    const citizens = document.getElementById("citizens");
    if (citizens) citizens.innerHTML = "";
    const audit = document.getElementById("audit");
    if (audit) audit.innerHTML = "";
    const result = document.getElementById("msg");
    if (result && result.classList.contains("ok")) {
      result.className = "result muted";
    }
  }
}

function logoutOfficer() {
  localStorage.removeItem("officerToken");
  localStorage.removeItem("officerUnit");
  localStorage.removeItem("officerUnitName");
  localStorage.removeItem("citizenToken");
  localStorage.removeItem("citizenPhone");
  renderSession();
  applyOfficerGate();
  showCitizenLogin();
  const box = document.getElementById("msg");
  if (box) { box.className = "result muted"; box.textContent = "Wylogowano."; }
}
function citizenToken() { return localStorage.getItem("citizenToken") || ""; }





function fmtPhone(raw) {
  const d = String(raw || "").replace(/\D/g, "");
  if (d.length === 11 && d.startsWith("48")) return "+48 " + d.slice(2,5) + " " + d.slice(5,8) + " " + d.slice(8);
  if (d.length === 9) return d.slice(0,3) + " " + d.slice(3,6) + " " + d.slice(6);
  return raw || "";
}
function fmtPlate(raw) {
  const p = String(raw || "").toUpperCase().replace(/\s+/g, "");
  const m = p.match(/^([A-Z]{2,3})([0-9].*)$/);
  return m ? m[1] + " " + m[2] : (raw || "");
}
function socialIcons(social) {
  if (!social) return "";
  const items = [
    ["fb", "Facebook", social.facebook],
    ["ig", "Instagram", social.instagram],
    ["x", "X", social.x_handle],
    ["in", "LinkedIn", social.linkedin],
    ["tt", "TikTok", social.tiktok],
  ].filter((x) => x[2]);
  if (!items.length) return '<div class="muted">Brak profili social</div>';
  return '<div class="social-icons">' + items.map(([id, label, url]) =>
    '<a class="soc" href="' + url + '" target="_blank" rel="noopener" title="' + label + '"><img src="img/' + id + '.svg" alt="' + label + '"></a>'
  ).join("") + "</div>";
}

function token() {
  return localStorage.getItem("officerToken") || "";
}

function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString("pl-PL");
}

function socialLine(social) { return socialIcons(social); }

async function api(path, opts = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (opts.auth) headers.Authorization = "Bearer " + token();
  if (opts.citizen) headers.Authorization = "Bearer " + citizenToken();
  const res = await fetch(API + path, Object.assign({}, opts, { headers }));
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

async function loginOfficer(ev) {
  ev.preventDefault();
  const box = document.getElementById("msg");
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: document.getElementById("user").value,
        password: document.getElementById("pass").value,
        unit_code: document.getElementById("unit").value,
      }),
    });
    localStorage.setItem("officerToken", data.access_token);
    localStorage.setItem("officerUnit", data.unit_code || "");
    localStorage.setItem("officerUnitName", data.unit_name || data.unit_code || "");
    renderSession();
    applyOfficerGate();
    box.className = "result ok";
    box.textContent = "Zalogowano: " + (data.unit_name || data.unit_code);

  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}

async function lookupVehicle(ev) {
  ev.preventDefault();
  const box = document.getElementById("msg");
  try {
    const q = document.getElementById("query").value.trim();
    const data = await api("/vehicles/" + encodeURIComponent(q), { auth: true });
    box.className = data.consent_contact ? "result ok" : "result err";
    const fleet = (data.vehicles || []).map(function (x) {
      return fmtPlate(x.plate) + (x.vin ? " (VIN: " + x.vin + ")" : "");
    }).join("<br>");
    box.innerHTML =
      "<strong>" + data.message + "</strong><br>" +
      "Szukane: " + fmtPlate(data.plate) + (data.vin ? " / VIN " + data.vin : "") + "<br>" +
      "Właściciel: " + data.owner_name + "<br>" +
      (data.phone ? 'Telefon: <a href="tel:' + String(data.phone).replace(/\D/g,"") + '">' + fmtPhone(data.phone) + "</a><br>" : "") +
      (data.email ? 'E-mail: <a href="mailto:' + data.email + '">' + data.email + "</a><br>" : "") +
      (data.city ? "Miejscowość: " + data.city + "<br>" : "") +
      (data.voivodeship ? "Województwo: " + data.voivodeship + "<br>" : "") +
      (data.unit ? "Właściwa komenda: " + data.unit.path + "<br>" : "") +
      (fleet ? "Pojazdy obywatela:<br>" + fleet + "<br>" : "") +
      socialLine(data.social);
  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}

async function loadAudit() {
  const box = document.getElementById("audit");
  try {
    const rows = await api("/audit", { auth: true });
    box.innerHTML = rows.map((r) =>
      "<tr><td>" + fmtTime(r.created_at) + "</td><td>" + r.actor + "</td><td>" + r.action + "</td><td>" + (r.plate || "") + "</td><td>" + (r.detail || "") + "</td></tr>"
    ).join("");
  } catch (e) {
    box.innerHTML = "<tr><td colspan='5'>" + e.message + "</td></tr>";
  }
}

async function registerCitizen(ev) {
  ev.preventDefault();
  const box = document.getElementById("msg");
  try {
    const logged = !!citizenToken();
    const data = await api(logged ? "/citizens/me" : "/citizens/register", {
      method: logged ? "PUT" : "POST",
      body: JSON.stringify({
        first_name: document.getElementById("fn").value,
        last_name: document.getElementById("ln").value,
        phone: document.getElementById("phone").value,
        email: document.getElementById("email") ? document.getElementById("email").value || null : null,
        plate: document.getElementById("plate").value,
        vin: document.getElementById("vin").value || null,
        city: document.getElementById("city").value || null,
        voivodeship: document.getElementById("voi").value || null,
        facebook: document.getElementById("fb").value || null,
        instagram: document.getElementById("ig").value || null,
        x_handle: document.getElementById("x").value || null,
        linkedin: document.getElementById("li").value || null,
        tiktok: document.getElementById("tt").value || null,
        consent_contact: document.getElementById("consent").checked,
      }),
      citizen: logged,
    });
    if (data.access_token) {
      localStorage.setItem("citizenToken", data.access_token);
      localStorage.setItem("citizenPhone", data.phone || document.getElementById("phone").value);
      renderSession();
    }
    box.className = "result ok";
    box.textContent = data.message;
  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}


async function loadCitizens() {
  const box = document.getElementById("citizens");
  const msg = document.getElementById("msg");
  try {
    const rows = await api("/admin/citizens", { auth: true });
    if (msg) { msg.className = "result ok"; msg.textContent = "Rekordów: " + rows.length; }
    box.innerHTML = rows.map((r) => {
      const plates = (r.vehicles || []).map(fmtPlate).join(", ") || "—";
      const soc = socialIcons(r);
      return "<tr><td>" + r.first_name + " " + r.last_name + "</td><td>" + fmtPhone(r.phone) +
        "</td><td>" + (r.consent_contact ? "tak" : "nie") + "</td><td>" + plates +
        "</td><td>" + (r.city || "—") + "</td><td>" + (r.unit || "—") + "</td><td>" + soc + "</td></tr>";
    }).join("");
  } catch (e) {
    if (msg) { msg.className = "result err"; msg.textContent = e.message; }
    box.innerHTML = "";
  }
}

async function exportXlsx() {
  const msg = document.getElementById("msg");
  try {
    const res = await fetch(API + "/admin/citizens.xlsx", {
      headers: { Authorization: "Bearer " + token() },
    });
    if (!res.ok) throw new Error("Eksport nieudany");
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "mundurovehdb_obywatele.xlsx";
    a.click();
    if (msg) { msg.className = "result ok"; msg.textContent = "Pobrano Excel."; }
  } catch (e) {
    if (msg) { msg.className = "result err"; msg.textContent = e.message; }
  }
}


let modalMode = null;
let citizenCache = null;

function showCitizenLogin() {
  const a = document.getElementById("citizenAppView");
  const b = document.getElementById("citizenLoginView");
  if (a) a.style.display = "none";
  if (b) b.style.display = "block";
  if (document.getElementById("citizenLoginView")) setNavVisible(false);
  closeModal();
}
function showCitizenApp() {
  const a = document.getElementById("citizenAppView");
  const b = document.getElementById("citizenLoginView");
  if (b) b.style.display = "none";
  if (a) a.style.display = "block";
  if (document.getElementById("citizenAppView")) setNavVisible(true);
}
function closeModal() {
  const m = document.getElementById("modal");
  if (m) m.hidden = true;
}
function openModal(title, html, mode) {
  document.getElementById("modalTitle").textContent = title;
  document.getElementById("modalBody").innerHTML = html;
  modalMode = mode;
  document.getElementById("modal").hidden = false;
}

function renderCitizenDashboard(data) {
  citizenCache = data;
  showCitizenApp();
  const person = document.getElementById("personCard");
  if (person) {
    const opts = (window._voi || []).map(function (v) {
      const sel = v.id === data.voivodeship ? " selected" : "";
      return '<option value="' + v.id + '"' + sel + '>' + v.label + '</option>';
    }).join("");
    person.innerHTML =
      '<div class="grid2"><div><label>Imię</label><input id="p_fn" value="' + (data.first_name||"") + '"></div>' +
      '<div><label>Nazwisko</label><input id="p_ln" value="' + (data.last_name||"") + '"></div></div>' +
      '<label>Telefon</label><input id="p_phone" value="' + (data.phone||"") + '">' +
      '<label>E-mail</label><input id="p_email" value="' + (data.email||"") + '">' +
      '<label>Miejscowość</label><input id="p_city" value="' + (data.city||"") + '">' +
      '<label>Województwo</label><select id="p_voi"><option value="">— wybierz —</option>' + opts + '</select>';
  }
  const vbox = document.getElementById("vehicleList");
  if (vbox) {
    const rows = data.vehicles || [];
    vbox.innerHTML = rows.length ? rows.map(function (v) {
      return '<div class="item"><div class="item-main"><div class="item-kicker">Pojazd</div><strong>' + fmtPlate(v.plate) + '</strong>' +
        '<div class="meta">' + (v.vin ? 'VIN ' + v.vin : 'brak VIN') + '</div></div><div class="acts">' +
        '<button class="ghost" type="button" onclick="openEditVehicle(\'' + v.plate + '\',\'' + (v.vin||'') + '\')">Edytuj</button>' +
        '<button class="danger" type="button" onclick="deleteVehicle(\'' + v.plate + '\')">Usuń</button></div></div>';
    }).join("") : '<div class="muted">Brak pojazdów</div>';
  }
  const sbox = document.getElementById("socialList");
  if (sbox) {
    const items = [
      ["facebook","fb","Facebook"],
      ["instagram","ig","Instagram"],
      ["x_handle","x","X"],
      ["linkedin","in","LinkedIn"],
      ["tiktok","tt","TikTok"],
    ];
    const have = items.filter(function (x) { return data[x[0]]; });
    sbox.innerHTML = have.length ? have.map(function (x) {
      return '<div class="item"><div class="social-icons"><a class="soc" href="' + data[x[0]] + '" target="_blank" rel="noopener"><img src="img/' + x[1] + '.svg" alt="' + x[2] + '"></a> ' + x[2] + '</div>' +
        '<div class="acts"><button class="secondary" type="button" onclick="deleteSocial(\'' + x[0] + '\')">Usuń</button></div></div>';
    }).join("") : '<div class="muted">Brak profili social</div>';
  }
}

async function loadCitizenDashboard() {
  try {
    const data = await api("/citizens/me", { citizen: true });
    renderCitizenDashboard(data);
  } catch (e) {
    showCitizenLogin();
  }
}

function fillCitizenForm(data) {
  renderCitizenDashboard(data);
}

async function loginCitizen(ev) {
  ev.preventDefault();
  const box = document.getElementById("msg");
  try {
    const data = await api("/citizens/login", {
      method: "POST",
      body: JSON.stringify({ phone: document.getElementById("loginPhone").value }),
    });
    localStorage.setItem("citizenToken", data.access_token);
    localStorage.setItem("citizenPhone", data.phone);
    renderSession();
    renderCitizenDashboard(data);
    box.className = "result ok";
    box.textContent = data.message || "Zalogowano.";
  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}

function openVehicleModal() {
  openModal("Nowy pojazd",
    '<label>Numer rejestracyjny</label><input id="m_plate" required placeholder="WA12345">' +
    '<label>VIN</label><input id="m_vin" placeholder="opcjonalnie">',
    "vehicle");
}
function openSocialModal() {
  const d = citizenCache || {};
  openModal("Social media",
    '<div class="soc-field"><img src="img/fb.svg"><div><label>Facebook</label><input id="m_fb" value="' + (d.facebook||"") + '"></div></div>' +
    '<div class="soc-field"><img src="img/ig.svg"><div><label>Instagram</label><input id="m_ig" value="' + (d.instagram||"") + '"></div></div>' +
    '<div class="soc-field"><img src="img/x.svg"><div><label>X</label><input id="m_x" value="' + (d.x_handle||"") + '"></div></div>' +
    '<div class="soc-field"><img src="img/in.svg"><div><label>LinkedIn</label><input id="m_li" value="' + (d.linkedin||"") + '"></div></div>' +
    '<div class="soc-field"><img src="img/tt.svg"><div><label>TikTok</label><input id="m_tt" value="' + (d.tiktok||"") + '"></div></div>',
    "social");
}


function openProfileModal() {
  const d = citizenCache || {};
  const opts = (window._voi || []).map(function (v) {
    const sel = v.id === d.voivodeship ? " selected" : "";
    return '<option value="' + v.id + '"' + sel + '>' + v.label + '</option>';
  }).join("");
  openModal("Edycja profilu",
    '<div class="grid2"><div><label>Imię</label><input id="m_fn" value="' + (d.first_name||"") + '"></div>' +
    '<div><label>Nazwisko</label><input id="m_ln" value="' + (d.last_name||"") + '"></div></div>' +
    '<label>Telefon</label><input id="m_phone" value="' + (d.phone||"") + '">' +
    '<label>E-mail</label><input id="m_email" value="' + (d.email||"") + '">' +
    '<label>Miejscowość</label><input id="m_city" value="' + (d.city||"") + '">' +
    '<label>Województwo</label><select id="m_voi"><option value="">— wybierz —</option>' + opts + '</select>',
    "profile");
}
function openEditVehicle(plate, vin) {
  openModal("Edycja pojazdu",
    '<label>Numer rejestracyjny</label><input id="m_plate" value="' + plate + '">' +
    '<label>VIN</label><input id="m_vin" value="' + (vin||"") + '">' +
    '<input type="hidden" id="m_old_plate" value="' + plate + '">',
    "vehicle-edit");
}

async function submitModal() {
  const box = document.getElementById("msg");
  try {
    let data;
    if (modalMode === "vehicle") {
      data = await api("/citizens/me/vehicles", {
        method: "POST",
        citizen: true,
        body: JSON.stringify({
          plate: document.getElementById("m_plate").value,
          vin: document.getElementById("m_vin").value || null,
        }),
      });
    } else if (modalMode === "vehicle-edit") {
      const oldp = document.getElementById("m_old_plate").value;
      data = await api("/citizens/me/vehicles/" + encodeURIComponent(oldp), {
        method: "PUT",
        citizen: true,
        body: JSON.stringify({
          plate: document.getElementById("m_plate").value,
          vin: document.getElementById("m_vin").value || null,
        }),
      });
    } else if (modalMode === "profile") {
      data = await api("/citizens/me/profile", {
        method: "PUT",
        citizen: true,
        body: JSON.stringify({
          first_name: document.getElementById("m_fn").value,
          last_name: document.getElementById("m_ln").value,
          phone: document.getElementById("m_phone").value,
          email: document.getElementById("m_email").value || null,
          city: document.getElementById("m_city").value || null,
          voivodeship: document.getElementById("m_voi").value || null,
        }),
      });
      if (data.access_token) {
        localStorage.setItem("citizenToken", data.access_token);
        localStorage.setItem("citizenPhone", data.phone);
        renderSession();
      }
    } else {
      data = await api("/citizens/me/social", {
        method: "PUT",
        citizen: true,
        body: JSON.stringify({
          facebook: document.getElementById("m_fb").value,
          instagram: document.getElementById("m_ig").value,
          x_handle: document.getElementById("m_x").value,
          linkedin: document.getElementById("m_li").value,
          tiktok: document.getElementById("m_tt").value,
        }),
      });
    }
    closeModal();
    renderCitizenDashboard(data);
    box.className = "result ok";
    box.textContent = "Zapisano. Zmiana jest w audycie służby.";
  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}

async function deleteVehicle(plate) {
  if (!confirm("Usunąć pojazd " + plate + "?")) return;
  const data = await api("/citizens/me/vehicles/" + encodeURIComponent(plate), { method: "DELETE", citizen: true });
  renderCitizenDashboard(data);
  const box = document.getElementById("msg");
  box.className = "result ok";
  box.textContent = "Usunięto pojazd. Wpis w audycie służby.";
}
async function deleteSocial(field) {
  if (!confirm("Usunąć ten profil?")) return;
  const data = await api("/citizens/me/social/" + field, { method: "DELETE", citizen: true });
  renderCitizenDashboard(data);
  const box = document.getElementById("msg");
  box.className = "result ok";
  box.textContent = "Usunięto kanał. Wpis w audycie służby.";
}

async function deleteCitizen() {
  if (!confirm("Wycofać zgodę i ukryć pojazdy?")) return;
  const box = document.getElementById("msg");
  try {
    const data = await api("/citizens/me", { method: "DELETE", citizen: true });
    box.className = "result ok";
    box.textContent = data.message;
    logoutOfficer();
  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}


async function saveCitizenChanges() {
  const box = document.getElementById("msg");
  try {
    const data = await api("/citizens/me/profile", {
      method: "PUT",
      citizen: true,
      body: JSON.stringify({
        first_name: document.getElementById("p_fn").value,
        last_name: document.getElementById("p_ln").value,
        phone: document.getElementById("p_phone").value,
        email: document.getElementById("p_email").value || null,
        city: document.getElementById("p_city").value || null,
        voivodeship: document.getElementById("p_voi").value || null,
      }),
    });
    if (data.access_token) {
      localStorage.setItem("citizenToken", data.access_token);
      localStorage.setItem("citizenPhone", data.phone);
      renderSession();
    }
    renderCitizenDashboard(data);
    box.className = "result ok";
    box.textContent = "Zmiany zapisane. Wpis w audycie służby.";
  } catch (e) {
    box.className = "result err";
    box.textContent = e.message;
  }
}


async function exportAuditXlsx() {
  const msg = document.getElementById("msg");
  try {
    const res = await fetch(API + "/audit.xlsx", {
      headers: { Authorization: "Bearer " + token() },
    });
    if (!res.ok) throw new Error("Eksport audytu nieudany");
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "mundurovehdb_audyt.xlsx";
    a.click();
    if (msg) { msg.className = "result ok"; msg.textContent = "Pobrano logi audytu."; }
  } catch (e) {
    if (msg) { msg.className = "result err"; msg.textContent = e.message; }
  }
}
