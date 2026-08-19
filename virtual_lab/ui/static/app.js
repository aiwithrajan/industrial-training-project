const $ = (id) => document.getElementById(id);
let lastRun = null;
let playing = false;

function log(msg) {
  const el = $("log");
  const t = new Date().toLocaleTimeString();
  el.textContent = `[${t}] ${msg}\n` + el.textContent;
}

async function getJSON(url, opts) {
  const res = await fetch(url, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function setBadge(kind, text) {
  const el = $("badge");
  el.className = "badge " + kind;
  el.textContent = text;
}

function stats(summary) {
  const rows = [
    ["Outcome", summary.outcome],
    ["Success", summary.success ? "yes" : "no"],
    ["Time (s)", summary.duration_s],
    ["Path (m)", summary.path_length_m],
    ["Clearance (m)", summary.min_clearance_m],
    ["Throughput / hr", summary.throughput_items_per_hr],
  ];
  $("stats").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
}

function worldMap(world) {
  const c = $("view");
  const ctx = c.getContext("2d");
  const pad = 28;
  const sx = (c.width - 2 * pad) / world.width;
  const sy = (c.height - 2 * pad) / world.height;
  const X = (x) => pad + x * sx;
  const Y = (y) => c.height - (pad + y * sy);
  return { ctx, X, Y, sx, sy, pad };
}

function drawWorld(run, index) {
  const world = run.world;
  const { ctx, X, Y, sx } = worldMap(world);
  const c = $("view");
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.fillStyle = "#f4f7fb";
  ctx.fillRect(0, 0, c.width, c.height);
  ctx.strokeStyle = "#0f2c59";
  ctx.lineWidth = 2;
  ctx.strokeRect(X(0), Y(world.height), world.width * sx, world.height * (c.height - 56) / world.height);
  ctx.strokeRect(X(0), Y(world.height), X(world.width) - X(0), Y(0) - Y(world.height));

  ctx.fillStyle = "#1b6b93";
  world.obstacles.forEach((b) => {
    ctx.fillRect(X(b[0]), Y(b[3]), X(b[2]) - X(b[0]), Y(b[1]) - Y(b[3]));
  });

  ctx.fillStyle = "#d4a017";
  circle(ctx, X(world.start[0]), Y(world.start[1]), 6);
  ctx.fillStyle = "#0f2c59";
  circle(ctx, X(world.goal[0]), Y(world.goal[1]), 7);

  const n = Math.max(1, Math.min(index, run.path.length));
  const pts = run.path.slice(0, n);
  ctx.strokeStyle = run.summary.success ? "#1b6b93" : "#c44536";
  ctx.lineWidth = 3;
  ctx.beginPath();
  pts.forEach((p, i) => (i ? ctx.lineTo(X(p.x), Y(p.y)) : ctx.moveTo(X(p.x), Y(p.y))));
  ctx.stroke();

  const p = pts[pts.length - 1];
  if (p) {
    ctx.fillStyle = "#c44536";
    ctx.beginPath();
    ctx.save();
    ctx.translate(X(p.x), Y(p.y));
    ctx.rotate(-p.theta);
    ctx.moveTo(12, 0);
    ctx.lineTo(-8, 7);
    ctx.lineTo(-8, -7);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
    ctx.beginPath();
    ctx.arc(X(p.x), Y(p.y), world.radius * sx, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(196,69,54,0.45)";
    ctx.stroke();
  }
}

function circle(ctx, x, y, r) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function play(run) {
  lastRun = run;
  $("replay").disabled = false;
  playing = true;
  const t0 = performance.now();
  const dur = 2800;
  function frame(now) {
    if (!playing) return;
    const u = Math.min(1, (now - t0) / dur);
    const idx = Math.floor(1 + u * (run.path.length - 1));
    drawWorld(run, idx);
    setBadge("run", "Playing  " + Math.round(u * 100) + "%");
    if (u < 1) requestAnimationFrame(frame);
    else {
      playing = false;
      setBadge(run.summary.success ? "go" : "fail", run.summary.success ? "GOAL REACHED" : "FAILED  " + run.summary.outcome);
      stats(run.summary);
    }
  }
  requestAnimationFrame(frame);
}

function bars(data) {
  const keys = ["random", "adversarial", "mcmc"];
  $("bars").innerHTML = keys.map((k) => {
    const pct = Math.round((data[k].failure_rate || 0) * 100);
    return `<div class="row"><div>${k}</div><div class="track"><div class="fill" style="width:${pct}%"></div></div><div>${pct}%</div></div>`;
  }).join("");
}

async function boot() {
  const snap = await getJSON("/api/snapshot");
  const sel = $("scenario");
  snap.scenarios.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.id;
    o.textContent = s.id;
    o.dataset.notes = s.notes || "";
    sel.appendChild(o);
  });
  $("engines").innerHTML = Object.entries(snap.backends)
    .map(([k, on]) => `<div class="pill ${on ? "on" : "off"}">${k} ${on ? "ready" : "off"}</div>`)
    .join("");
  $("notes").textContent = sel.options[0]?.dataset.notes || "";
  sel.onchange = () => {
    $("notes").textContent = sel.selectedOptions[0].dataset.notes || "";
  };
  const bind = (id, label) => {
    $(id).oninput = () => ($(label).textContent = Number($(id).value).toFixed(2));
  };
  bind("speed", "speedVal");
  bind("friction", "fricVal");
  bind("noise", "noiseVal");
}

$("run").onclick = async () => {
  setBadge("run", "Simulating...");
  log("Running " + $("scenario").value);
  try {
    const run = await getJSON("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: $("scenario").value,
        use_cbf: $("cbf").checked,
        speed: Number($("speed").value),
        friction: Number($("friction").value),
        sensor_noise: Number($("noise").value),
      }),
    });
    stats(run.summary);
    log(run.summary.outcome + " in " + run.summary.duration_s + "s");
    play(run);
  } catch (err) {
    setBadge("fail", String(err.message));
    log(err.message);
  }
};

$("replay").onclick = () => lastRun && play(lastRun);

$("search").onclick = async () => {
  log("Adversarial search (this takes a few seconds)...");
  setBadge("run", "Searching failures...");
  try {
    const data = await getJSON("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: $("scenario").value, trials: 8 }),
    });
    bars(data);
    log("Adversarial " + data.adversarial.failure_rate + " vs random " + data.random.failure_rate);
    setBadge("go", "Search complete");
  } catch (err) {
    setBadge("fail", err.message);
  }
};

$("tune").onclick = async () => {
  log("Bayesian speed tuning...");
  setBadge("run", "Tuning...");
  try {
    const data = await getJSON("/api/tune", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: $("scenario").value }),
    });
    $("tuneOut").textContent = `Best speed ${data.best_speed} m/s  |  +${data.improvement_pct}% vs baseline ${data.baseline_score}`;
    log("Tune " + JSON.stringify({ speed: data.best_speed, improvement: data.improvement_pct }));
    setBadge("go", "Tuned");
  } catch (err) {
    setBadge("fail", err.message);
  }
};

boot().catch((err) => log(err.message));
