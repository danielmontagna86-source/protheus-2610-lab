// Login de conta Google para o Gemini CLI, conduzido pelo "lab setup" (sem a tela interativa do CLI).
// Faz o mesmo fluxo do CLI com NO_BROWSER=true (OAuth "aplicativo instalado" + PKCE, redirect
// codeassist.google.com/authcode) e grava a credencial onde o CLI a le (~/.gemini/oauth_creds.json).
// Cliente OAuth e escopos sao lidos do pacote instalado do Gemini CLI: nada disso fica no repositorio.
// Nunca imprime codigo nem token. Saida: 0 ok; 1 erro do Google ou de rede; 2 uso/ambiente.
// author: daniel.montagna
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline";

const pacote = process.argv[2];
if (!pacote || !fs.existsSync(pacote)) {
  console.error("uso: gemini_oauth.mjs <pasta do pacote @google/gemini-cli>");
  process.exit(2);
}

function lerConfig() {
  const dir = path.join(pacote, "bundle");
  for (const nome of fs.readdirSync(dir).filter((n) => n.endsWith(".js"))) {
    const txt = fs.readFileSync(path.join(dir, nome), "utf8");
    const id = txt.match(/var OAUTH_CLIENT_ID = "([^"]+)"/);
    const segredo = txt.match(/var OAUTH_CLIENT_SECRET = "([^"]+)"/);
    const escopo = txt.match(/var OAUTH_SCOPE = \[([^\]]+)\]/);
    if (id && segredo && escopo) {
      return { clientId: id[1], clientSecret: segredo[1], scopes: [...escopo[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]) };
    }
  }
  return null;
}

const cfg = lerConfig();
if (!cfg) {
  console.error("  gemini: cliente OAuth nao encontrado no pacote do Gemini CLI (versao mudou?)");
  process.exit(2);
}
const redirectUri = "https://codeassist.google.com/authcode";
const b64url = (buf) => buf.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const verifier = b64url(crypto.randomBytes(48));
const challenge = b64url(crypto.createHash("sha256").update(verifier).digest());
const state = crypto.randomBytes(32).toString("hex");
const url = "https://accounts.google.com/o/oauth2/v2/auth?" + new URLSearchParams({
  redirect_uri: redirectUri,
  access_type: "offline",
  prompt: "consent",
  scope: cfg.scopes.join(" "),
  code_challenge_method: "S256",
  code_challenge: challenge,
  state,
  response_type: "code",
  client_id: cfg.clientId,
}).toString();

console.log("\n  1. Abra esta URL no navegador do seu computador (copie a linha inteira):\n");
console.log(url + "\n");
console.log("  2. Entre com sua conta Google e autorize; o Google mostra um codigo.");
console.log("     (sem limite de tempo aqui; o codigo do Google vale poucos minutos depois de gerado)");

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });
process.stdout.write("  3. Cole o codigo aqui e tecle Enter: ");
const bruto = await new Promise((ok) => rl.once("line", ok));
rl.close();
// Terminais podem embrulhar a colagem em sequencias de controle (bracketed paste) ou trazer \r.
const codigo = String(bruto || "").replace(/\x1b\[[0-9;]*~?/g, "").replace(/[\x00-\x1f\x7f]/g, "").trim();
if (!codigo) {
  console.error("  gemini: nenhum codigo informado");
  process.exit(1);
}

let resp;
try {
  resp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code: codigo,
      code_verifier: verifier,
      client_id: cfg.clientId,
      client_secret: cfg.clientSecret,
      redirect_uri: redirectUri,
      grant_type: "authorization_code",
    }),
  });
} catch (e) {
  console.error(`  gemini: falha de rede ao trocar o codigo: ${e.cause?.code || e.message}`);
  process.exit(1);
}
const dados = await resp.json().catch(() => ({}));
if (!resp.ok || !dados.access_token) {
  // So o codigo e a descricao do erro do Google; nada do pedido.
  console.error(`  gemini: o Google recusou o codigo: ${dados.error || resp.status}${dados.error_description ? " (" + dados.error_description + ")" : ""}`);
  process.exit(1);
}
if (!dados.refresh_token) {
  console.error("  gemini: o Google nao devolveu refresh_token; o login expiraria em 1 hora. Refaca autorizando de novo.");
  process.exit(1);
}

const dirGemini = path.join(os.homedir(), ".gemini");
fs.mkdirSync(dirGemini, { recursive: true });
const credenciais = {
  access_token: dados.access_token,
  refresh_token: dados.refresh_token,
  scope: dados.scope,
  token_type: dados.token_type,
  id_token: dados.id_token,
  expiry_date: Date.now() + (Number(dados.expires_in) || 3600) * 1000,
};
const destino = path.join(dirGemini, "oauth_creds.json");
const tmp = destino + ".plab.tmp";
fs.writeFileSync(tmp, JSON.stringify(credenciais, null, 2), { mode: 0o600 });
fs.renameSync(tmp, destino);
fs.chmodSync(destino, 0o600);

// Conta ativa, como o CLI faz depois do login (so o e-mail; usado na tela do CLI).
try {
  const ui = await fetch("https://www.googleapis.com/oauth2/v2/userinfo", { headers: { Authorization: `Bearer ${dados.access_token}` } });
  if (ui.ok) {
    const { email } = await ui.json();
    const arq = path.join(dirGemini, "google_accounts.json");
    let contas = { active: null, old: [] };
    try { contas = JSON.parse(fs.readFileSync(arq, "utf8")); } catch {}
    if (contas.active && contas.active !== email) contas.old = [...new Set([...(contas.old || []), contas.active])];
    contas.old = (contas.old || []).filter((e) => e !== email);
    contas.active = email;
    fs.writeFileSync(arq, JSON.stringify(contas, null, 2));
  }
} catch {}
console.log("  gemini: login Google concluido (credencial em ~/.gemini/oauth_creds.json, permissao 600)");
