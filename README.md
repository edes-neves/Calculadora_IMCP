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
- **Histórico**: todas as medições por paciente, com opção de limpar.
- **Evolução**: gráfico de linha com a trajetória do IMC ao longo do tempo.
- **Meta de peso**: define uma meta por paciente e mostra a distância até ela.
- **Exportar PDF**: relatório profissional com os dados da medição, composição corporal e recomendação personalizada.
- **Exportar dados**: exporta todos os perfis e medições em **CSV** ou **JSON** (menu Arquivo).
- **Backup automático**: ao fechar o app, um backup compactado (.zip) do banco é salvo na pasta `backups/` (roteação automática das últimas 10 cópias).
- **Envio por e-mail (opcional)**: é possível configurar SMTP no menu Arquivo → Configurações para receber o backup por e-mail. As credenciais ficam salvas em `config_smtp.json` (fora do Git). Deixe os campos vazios para desativar.

## Configuração do envio por e-mail

1. No menu **Arquivo → Configurações**, preencha servidor SMTP, porta, usuário, senha de aplicativo e destinatário.
2. Marque **"Ativar envio automático"** (e **STARTTLS** se o servidor usar, como o Gmail na porta 587).
3. Clique em **Testar envio** para validar antes de usar.
4. Ao fechar o app, o backup .zip é enviado para o e-mail configurado (além de salvo localmente).

> Dica (Gmail): gere uma "Senha de aplicativo" em Conta Google → Segurança, e use a porta 587 com STARTTLS.

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
# Testes da camada de dados e dos cálculos
python -m unittest test_database -v

# Testes de interface (parsing de entrada, fluxo de cálculo e PDFs)
python -m unittest test_ui -v

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

| Arquivo          | Descrição                                                      |
|------------------|----------------------------------------------------------------|
| `main.py`        | Interface gráfica (CustomTkinter) e orquestração da aplicação  |
| `database.py`    | Camada de dados SQLite (perfis, histórico, cálculos e regras)  |
| `grafico.py`     | Geração das imagens (barra de faixas e gráfico de evolução)    |
| `relatorio.py`   | Geração do relatório em PDF (ReportLab)                        |
| `test_database.py` | Testes unitários da camada de dados e cálculos               |
| `calculadora_imc.db` | Banco SQLite gerado pelo app                                 |

> Observação: ao abrir pela primeira vez após a atualização, o app migra
> automaticamente o banco antigo (histórico sem perfil) para um "Perfil padrão",
> preservando os registros existentes.