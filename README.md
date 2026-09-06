# Calculadora de IMC Profissional

Aplicação desktop (Python + CustomTkinter) para calcular o IMC com classificação
oficial da **OMS** para adultos e da **SBGG/OPAS** para idosos (≥ 60 anos), com
gerenciamento de pacientes, histórico, gráfico de evolução, metas de peso e
exportação de relatório em PDF.

## Funcionalidades

- **Perfis / Pacientes**: cadastro, edição e exclusão de pessoas com nome, idade e gênero. Ao clicar em **Editar**, os dados do perfil selecionado são carregados no formulário para alteração e salvamento.
- **Visão geral (dashboard)**: resumo do perfil ativo com último IMC, classificação, peso e meta, além da tendência do IMC ao longo das medições.
- **Busca de pacientes**: campo de pesquisa que filtra a lista de perfis em tempo real.
- **Cálculo do IMC**: seletor de perfil na própria aba (ordenado por cadastro), indicador visual em barra de faixas coloridas (OMS/SBGG) e faixa de peso ideal.
- **Validação de entrada**: limites realistas para peso, altura e idade; aceita vírgula como separador decimal; atalho para entrada em centímetros.
- **Composição corporal**: campos opcionais de cintura e quadril para estimar a % de gordura corporal (fórmula de Deurenberg), o RCQ e o risco cardiovascular pela circunferência da cintura (OMS).
- **Gasto energético (TMB e GET)**: calcula a Taxa Metabólica Basal pelas equações de **Mifflin-St Jeor** e **Harris-Benedict** e o Gasto Energético Total pela aplicação do **fator de atividade** (sedentário a atleta). Disponível para pacientes adultos (18+). Os valores são exibidos na tela de cálculo, salvos no histórico, exportados (CSV/JSON) e incluídos no relatório PDF.
- **Histórico**: todas as medições por paciente, com seletor de perfil e opção de limpar.
- **Evolução**: gráfico de linha com a trajetória do IMC ao longo do tempo, com seletor de perfil e exportação do gráfico em PDF.
- **Meta de peso**: define uma meta por paciente e mostra a distância até ela.
- **Exportar PDF**: relatório profissional com os dados da medição, composição corporal e recomendação personalizada.
- **Exportar dados**: exporta todos os perfis e medições em **CSV** ou **JSON** (menu Arquivo).
- **Tema claro/escuro**: alternância rápida pelo botão no topo ou pelo menu **Exibir → Alternar tema**.
- **Menus e atalhos**: barra de menus com **Arquivo** (exportar/PDF, configurações, sair), **Editar** (novo/editar/excluir perfil), **Exibir** (tema), **Históricos** e **Ajuda**.
- **Ajuda por e-mail**: menu **Ajuda → Relatar um problema / Enviar uma sugestão / Contato** abre o cliente de e-mail pré-preenchido; **Sobre** mostra versão, desenvolvedor e licença MIT.
- **Backup**: ao fechar o app, ele pergunta se você deseja criar um backup compactado (.zip) do banco na pasta `backups/` (roteação automática das últimas 10 cópias).
- **Atualização automática**: ao iniciar, o app consulta as **releases no GitHub**; se houver versão mais nova, avisa com as notas da atualização e permite **baixar e aplicar com um clique** (disponível na versão executável; ver seção abaixo).
- **Envio por e-mail (opcional)**: é possível configurar SMTP no menu Arquivo → Configurações para receber o backup por e-mail. A senha fica salva **cifrada** em `config_smtp.json` (fora do Git). Deixe os campos vazios para desativar.

## Configuração do envio por e-mail

1. No menu **Arquivo → Configurações**, preencha servidor SMTP, porta, usuário, senha de aplicativo e destinatário.
2. Marque **"Ativar envio automático"** (e **STARTTLS** se o servidor usar, como o Gmail na porta 587).
3. Clique em **Testar envio** para validar antes de usar.
4. Ao fechar o app e confirmar o backup, o .zip é enviado para o e-mail configurado (além de salvo localmente).

> Dica (Gmail): gere uma "Senha de aplicativo" em Conta Google → Segurança, e use a porta 587 com STARTTLS.

## Atualização automática (GitHub Releases)

Na versão executável (AppImage ou binário PyInstaller), o app verifica no
GitHub se existe uma release mais nova que a versão instalada:

1. **Ao iniciar**, a verificação acontece em segundo plano (sem travar a UI).
2. Se houver versão nova, uma janela mostra **o que há de novo** com os botões:
   **Atualizar agora** (baixa e aplica na hora, reiniciando o app), **Agora não**
   (pergunta de novo no próximo início) e **Pular esta versão** (não oferece mais
   aquela versão).
3. Também é possível verificar manualmente pelo menu **Ajuda → Verificar atualizações**.

O download ocorre com barra de progresso e novo binário substitui o executável
atual automaticamente. Em caso de permissão (ex.: AppImage em pasta sem escrita)
ou falha de rede, o app informa a URL para baixar manualmente.

**Como publicar uma nova versão** (para que os usuários recebam a atualização):

1. Atualize a constante `VERSAO_ATUAL` em `atualizador.py` (ex.: `1.2.0`).
2. Gere o executável/AppImage (`./build.sh` + AppImage).
3. Crie uma **Release** no GitHub com a tag `v1.2.0` (a versão deve ser **maior**
   que a constante do app) e **anexe o AppImage** como asset da release.

> Automatize tudo com o `github.sh`: `./github.sh 1.2.0` atualiza a versão,
> roda os testes, gera o executável e o AppImage, faz commit + push e publica a
> Release `v1.2.0` com o AppImage anexado. Opções: `--skip-build`,
> `--skip-package` e `--skip-tests`. Veja `./github.sh --help`.

## Logs e tratamento de erros

- Exceções não capturadas são registradas em `logs/app_<data>.log` (não versionados no Git) com data/hora e stack trace, e uma janela amigável é exibida.
- Eventos importantes (backups, exportações) também são registrados para auditoria.

## Como rodar

```bash
# 1. Criar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar
python main.py
```

## Como testar

```bash
# Testes da camada de dados e cálculos (perfis, IMC, composição corporal, TMB/GET)
python -m unittest test_database -v

# Testes de interface (parsing de entrada, fluxo de cálculo, PDF, dashboard, busca)
python -m unittest test_ui -v

# Testes de backup (local, rotação e exportação CSV/JSON)
python -m unittest test_backup -v

# Testes das equações nutricionais (TMB/GET) e da persistência delas
python -m unittest test_nutricao -v

# Testes de logging e tratamento de erros
python -m unittest test_logger -v

# Testes da configuração SMTP (senha cifrada em repouso)
python -m unittest test_config -v

# Testes do verificador de atualizações (versões e assets do GitHub)
python -m unittest test_atualizador -v

# Rodar todos os testes
python -m unittest discover -v
```

## Como gerar o executável (build)

```bash
pip install -r requirements-dev.txt   # inclui o PyInstaller
./build.sh                              # Linux/macOS
# ou:
python -m PyInstaller CalculadoraIMC.spec --noconfirm
```

O executável único (com a interface, o ícone e todas as dependências) é gerado
em `dist/CalculadoraIMC`.

## Estrutura

| Arquivo            | Descrição                                                      |
|--------------------|----------------------------------------------------------------|
| `main.py`          | Interface gráfica (CustomTkinter) e orquestração da aplicação  |
| `database.py`      | Camada de dados SQLite (perfis, histórico, cálculos e regras)  |
| `grafico.py`       | Geração das imagens (barra de faixas e gráfico de evolução)    |
| `relatorio.py`     | Geração do relatório em PDF (ReportLab)                        |
| `nutricao.py`      | Cálculos nutricionais: TMB (Mifflin/Harris) e GET (fator ativ.)|
| `backup.py`        | Backup .zip local, rotação e envio por e-mail (SMTP)           |
| `config.py`        | Persistência das configurações SMTP (`config_smtp.json`)       |
| `logger.py`        | Logs em arquivo e exception hook global                        |
| `caminhos.py`      | Resolução dos diretórios de dados (dev x AppImage)             |
| `atualizador.py`   | Verificação/atualização automática via GitHub Releases          |
| `test_database.py` | Testes unitários da camada de dados e cálculos                 |
| `test_ui.py`       | Testes da interface (parsing, cálculo, PDF, dashboard, busca)  |
| `test_backup.py`   | Testes do backup e da exportação CSV/JSON                      |
| `test_nutricao.py` | Testes das equações de TMB/GET e sua persistência              |
| `test_logger.py`   | Testes do logging e do tratamento de erros                     |
| `test_config.py`   | Testes da configuração SMTP (senha cifrada em repouso)         |
| `test_atualizador.py` | Testes de versões e escolha de asset do atualizador          |
| `CalculadoraIMC.spec` | Configuração de build do PyInstaller                        |
| `build.sh`         | Script de build do executável                                  |
| `github.sh`        | Script de publicação: bump de versão, build, push e Release    |
| `CalculadoraIMC.desktop` | Atalho do AppImage (com `StartupWMClass`)                |
| `AppRun`            | Ponto de entrada do AppImage (executa o binário)               |
| `icone.png`        | Ícone da aplicação                                             |
| `calculadora_imc.db` | Banco SQLite gerado pelo app em execução                     |

> Observação: ao abrir pela primeira vez após a atualização, o app migra
> automaticamente o banco antigo (histórico sem perfil) para um "Perfil padrão",
> preservando os registros existentes.

## Como gerar um AppImage (Linux)

O AppImage é um executável autossuficiente que roda em qualquer distribuição Linux
sem instalação. Pré-requisitos: `wget`, `unzip`, `python3-venv`, e o Kit de
Desenvolvimento (Qt, GDK, etc.) para gerar o executável via PyInstaller.

```bash
# 1. Gerar o executável com PyInstaller (já contém todas as dependências)
python -m PyInstaller CalculadoraIMC.spec --noconfirm

# 2. Baixar o appimagetool
wget -O appimagetool \
  "https://github.com/AppImage/AppImageKit/releases/latest/download/appimagetool-x86_64.AppImage"
chmod +x appimagetool

# 3. Montar a estrutura AppDir
mkdir -p AppDir/usr/bin
cp dist/CalculadoraIMC AppDir/usr/bin/
cp icone.png AppDir/
cp CalculadoraIMC.desktop AppDir/
cp AppRun AppDir/          # AppRun obrigatório (executa o binário)

# 4. Empacotar
./appimagetool AppDir
# gera: Calculadora_de_IMC_Profissional-x86_64.AppImage
```

> Importante: copie o binário **novo** (`cp dist/CalculadoraIMC AppDir/usr/bin/`) antes
> de cada empacotamento. Se o AppDir mantiver um binário antigo, o AppImage será
> gerado sem as mudanças mais recentes do código. Para garantir, refaça o build
> (passo 1) antes do passo 3.

O `AppRun` é o ponto de entrada do AppImage e executa o binário PyInstaller:

```sh
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE" || exit 1
exec "$HERE/usr/bin/CalculadoraIMC" "$@"
```

O arquivo de atalho `CalculadoraIMC.desktop` (versionado na raiz do projeto) já
inclui o `StartupWMClass=CalculadoraDeIMCProfissional`, que permite aos
gerenciadores de janela agrupar e aplicar o tema correto à janela do app:

```ini
[Desktop Entry]
Type=Application
Name=Calculadora de IMC Profissional
Comment=Calculadora de IMC com classificação OMS
Exec=CalculadoraIMC
Icon=icone
Terminal=false
Categories=Utility;
StartupWMClass=CalculadoraDeIMCProfissional
StartupNotify=true
```

> Em desenvolvimento, o app usa a pasta do projeto. No executável e no AppImage,
> o banco, os logs, as configs SMTP e os backups são guardados em
> `~/.local/share/CalculadoraIMC/` (persistente e gravável), nunca dentro do
> pacote temporário.