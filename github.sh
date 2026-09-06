#!/usr/bin/env bash
# Publica uma nova versão da Calculadora de IMC Profissional.
#
# Fluxo:
#   1. Define a nova versão (argumento ou pergunta)
#   2. Valida que é maior que a VERSAO_ATUAL em atualizador.py
#   3. Atualiza a VERSAO_ATUAL e roda os testes
#   4. Gera o executável (PyInstaller) e empacota o AppImage
#   5. Faz commit e push para main
#   6. Cria a Release vX.Y.Z no GitHub com o AppImage anexado
#
# Uso:  ./github.sh [X.Y.Z] [--skip-build] [--skip-package] [--skip-tests]
#       PYTHON=python ./github.sh 1.2.0
set -euo pipefail
cd "$(dirname "$0")"

REPO="edes-neves/Calculadora_IMCP"
APPIMAGE="Calculadora_de_IMC_Profissional-x86_64.AppImage"
PY=${PYTHON:-.venv/bin/python}

SKIP_BUILD=0
SKIP_PACKAGE=0
SKIP_TESTS=0
NOVA_VERSION=""

for arg in "$@"; do
    case "$arg" in
        --skip-build)   SKIP_BUILD=1 ;;
        --skip-package) SKIP_PACKAGE=1 ;;
        --skip-tests)   SKIP_TESTS=1 ;;
        -h|--help)      sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *)              NOVA_VERSION="$arg" ;;
    esac
done

command -v gh >/dev/null || { echo "Erro: CLI 'gh' não instalado." >&2; exit 1; }

versao_maior() {
    local IFS=.
    read -r -a a <<< "$1"
    read -r -a b <<< "$2"
    for i in 0 1 2; do
        local la=$((10#${a[i]:-0})) lb=$((10#${b[i]:-0}))
        if (( la > lb )); then return 0; fi
        if (( la < lb )); then return 1; fi
    done
    return 1
}

ATUAL=$(grep '^VERSAO_ATUAL' atualizador.py | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
echo "==> Versão atual no código: $ATUAL"

if [ -z "$NOVA_VERSION" ]; then
    read -r -p "==> Nova versão (ex.: 1.2.0): " NOVA_VERSION
fi
if ! [[ "$NOVA_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Erro: versão inválida '$NOVA_VERSION' (use o formato X.Y.Z)." >&2
    exit 1
fi
if ! versao_maior "$NOVA_VERSION" "$ATUAL"; then
    echo "Erro: $NOVA_VERSION não é maior que a versão atual ($ATUAL)." >&2
    exit 1
fi

echo "==> Atualizando VERSAO_ATUAL para $NOVA_VERSION"
sed -i "s/^VERSAO_ATUAL = .*/VERSAO_ATUAL = \"$NOVA_VERSION\"/" atualizador.py

if [ "$SKIP_TESTS" -eq 0 ]; then
    echo "==> Rodando testes"
    "$PY" -m unittest discover
fi

if [ "$SKIP_BUILD" -eq 0 ]; then
    echo "==> Gerando executável com PyInstaller"
    "$PY" -m PyInstaller CalculadoraIMC.spec --noconfirm
else
    echo "==> Pulando build (--skip-build)"
fi

if [ "$SKIP_PACKAGE" -eq 0 ]; then
    echo "==> Montando o AppImage"
    cp -f dist/CalculadoraIMC AppDir/usr/bin/
    ./appimagetool AppDir
    chmod +x "$APPIMAGE"
else
    echo "==> Pulando o empacotamento (--skip-package)"
fi
[ -f "$APPIMAGE" ] || { echo "Erro: $APPIMAGE não encontrado." >&2; exit 1; }

echo "==> Commit e push"
git add -A
git commit -m "Versão $NOVA_VERSION"
git push origin main

NOTAS_FILE=$(mktemp)
{
    ULTIMA_TAG=$(git tag --sort=-v:refname | head -1 || true)
    if [ -n "$ULTIMA_TAG" ]; then
        echo "## O que há de novo"
        git log --oneline --no-merges "$ULTIMA_TAG"..HEAD | sed 's/^/- /'
    fi
    echo
    echo "## Como instalar/atualizar"
    echo
    echo '```bash'
    echo "chmod +x $APPIMAGE"
    echo "./$APPIMAGE"
    echo '```'
} > "$NOTAS_FILE"

echo "==> Criando a release v$NOVA_VERSION no GitHub"
gh release create "v$NOVA_VERSION" "$APPIMAGE" \
    --repo "$REPO" \
    --title "v$NOVA_VERSION" \
    --notes-file "$NOTAS_FILE"
rm -f "$NOTAS_FILE"

echo
echo "Pronto! Release publicada:"
gh release view "v$NOVA_VERSION" --repo "$REPO" --json url,assets -q '.url'