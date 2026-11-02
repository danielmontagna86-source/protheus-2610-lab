"""Scanner auxiliar de compartilhamento; não é DLP completo. author: daniel.montagna."""
import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ALLOWED_FOLDERS = {"references", "scripts", "assets", "tests"}
ALLOWED_SUFFIXES = {".md", ".py", ".json"}
PUBLIC_HOSTS = {"totvs.github.io", "github.com", "tdn.totvs.com", "www.gov.br", "docs.python.org", "po-ui.io", "antigravity.google", "www.antigravity.google", "codelabs.developers.google.com", "playwright.dev"}


def validate(root):
    root = Path(root).resolve()
    errors = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return ["SKILL.md ausente"]
    entry = skill.read_text(encoding="utf-8")
    if not re.match(r"\A---\nname: testes-protheus\ndescription: [^\n]+\n---\n", entry):
        errors.append("Frontmatter inválido")
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append(f"Link/escape não permitido: {relative}")
            continue
        if path.is_dir():
            if relative.parts[0] not in ALLOWED_FOLDERS:
                errors.append(f"Diretório fora do pacote: {relative}")
            continue
        if len(relative.parts) == 1 and relative.name not in {"SKILL.md", "README.md"}:
            errors.append(f"Arquivo raiz inesperado: {relative}")
        if path.suffix not in ALLOWED_SUFFIXES or any(
            part.startswith(".") or "__pycache__" in part or ".bak" in part.lower()
            for part in relative.parts
        ):
            errors.append(f"Arquivo proibido: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"Não é texto UTF-8: {relative}")
            continue
        if "daniel.montagna" not in content:
            errors.append(f"Autoria ausente: {relative}")
        if re.search(r"[A-Za-z]:[/\\]Users[/\\]|file:" + "//", content):
            errors.append(f"Caminho local de usuário: {relative}")
        if re.search(r'(?i)["\'](?:password|senha|token|api_key)["\']\s*:\s*["\'][^"\']+["\']', content):
            errors.append(f"Possível segredo em atribuição: {relative}")
        for url in re.findall(r'https?://[^\s<>\)"\']+', content):
            host = urlparse(url).hostname
            if host not in PUBLIC_HOSTS and not (host and (host == "example.com" or host.endswith(".example.com"))):
                errors.append(f"Endpoint fora de allowlist pública: {relative}")
        if path.suffix == ".py":
            try:
                ast.parse(content, filename=str(relative))
            except SyntaxError:
                errors.append(f"Sintaxe Python inválida: {relative}")
        elif path.suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError:
                errors.append(f"JSON inválido: {relative}")
        elif path.suffix == ".md":
            for target in re.findall(r'\]\(([^\)]+)\)', content):
                target = target.strip("<>").split("#", 1)[0]
                if target and not re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    if not (path.parent / target).is_file():
                        errors.append(f"Referência ausente: {relative} -> {target}")
    return errors


if __name__ == "__main__":
    issues = validate(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    print(json.dumps({"author": "daniel.montagna", "ok": not issues, "errors": issues}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if issues else 0)
