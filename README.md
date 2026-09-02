# Calculadora de IMC Profissional

Aplicação desktop (Python + CustomTkinter) para calcular o IMC com classificação
oficial da **OMS** para adultos e da **SBGG/OPAS** para idosos (≥ 60 anos), com
gerenciamento de pacientes, histórico, gráfico de evolução, metas de peso e
exportação de relatório em PDF.

## Funcionalidades

- **Perfis / Pacientes**: cadastro, edição e exclusão de pessoas com nome, idade e gênero. Ao clicar em **Editar**, os dados do perfil selecionado são carregados no formulário para alteração e salvamento.
- **Cálculo do IMC**: seletor de perfil na própria aba (ordenado por cadastro), indicador visual em barra de faixas coloridas (OMS/SBGG) e faixa de peso ideal.
- **Validação de entrada**: limites realistas para peso, altura e idade; aceita vírgula como separador decimal; atalho para entrada em centímetros.
- **Histórico**: todas as medições por paciente, com opção de limpar.
- **Evolução**: gráfico de linha com a trajetória do IMC ao longo do tempo.
- **Meta de peso**: define uma meta por paciente e mostra a distância até ela.
- **Exportar PDF**: relatório profissional com os dados da medição.

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
python -m unittest test_database -v
```

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