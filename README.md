# Browser Task Automation

> Reads a list of tasks from a spreadsheet and automatically assigns them to specific responsible parties through a web interface — saving dozens of hours in a team's weekly workflow.

Built with Python and Selenium. The automation handles the full cycle: opens the browser, logs in, searches for each record, assigns the correct category, and saves progress — resuming exactly where it left off if interrupted.

---

## Features

- **Progress recovery** — completed tasks are cached in CSV, so the process can be interrupted and resumed without redoing work
- **Session management** — automatically detects if the browser is already open and reconnects instead of starting over
- **Selector obfuscation** — web selectors are base64-encoded at rest, keeping the target system private (see `web_paths.sample.py`)
- **Rotating logs** — full trace log with automatic rotation, keeping disk usage under control
- **Automatic ChromeDriver management** — always installs the correct driver version for the current Chrome installation

---

## Stack

- Python 3
- Selenium
- Pandas
- WebDriver Manager

---

## Project Structure

```
browser-task-automation/
├── core/
│   ├── ferramentas.py        # Connection, logging, environment setup
│   ├── web_paths.py          # Obfuscated web selectors
│   ├── web_paths.sample.py   # Sample selector structure (for reference)
│   ├── primeira_pagina.py    # First page interactions
│   └── segunda_pagina.py     # Second page interactions
├── input/
│   ├── url.txt               # Target URL (not versioned)
│   └── tabelas_a_processar/  # Spreadsheets to process (not versioned)
├── output/                   # Logs and progress cache (not versioned)
├── encode_selector.sample.py # How to generate obfuscated selectors
└── main.py
```

---

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Copy `encode_selector.sample.py`, fill in your selectors, run it and paste the output into `web_paths.py`
4. Add the target URL to `input/url.txt`
5. Place your spreadsheets in `input/tabelas_a_processar/`
6. Run:
```bash
python main.py
```

---

## Notes

- Developed and actively used in a real work environment
- The target system is intentionally kept private at the team's request
- Selector obfuscation is a conscious architectural decision, not a workaround

---

---

# Browser Task Automation

> Lê uma lista de tarefas a partir de uma planilha e as atribui automaticamente a responsáveis específicos através de uma interface web — economizando dezenas de horas no fluxo de trabalho semanal de uma equipe.

Construído com Python e Selenium. A automação cobre o ciclo completo: abre o navegador, realiza o login, pesquisa cada registro, atribui a categoria correta e salva o progresso — retomando exatamente de onde parou em caso de interrupção.

---

## Funcionalidades

- **Recuperação de progresso** — tarefas concluídas são salvas em CSV, permitindo interromper e retomar sem reprocessar o que já foi feito
- **Gerenciamento de sessão** — detecta automaticamente se o navegador já está aberto e reconecta, sem iniciar do zero
- **Ofuscação de seletores** — os seletores web são armazenados em base64, mantendo o sistema-alvo privado (veja `web_paths.sample.py`)
- **Logs rotativos** — log completo com rotação automática, mantendo o uso de disco sob controle
- **Gerenciamento automático do ChromeDriver** — instala sempre a versão correta do driver para a instalação atual do Chrome

---

## Stack

- Python 3
- Selenium
- Pandas
- WebDriver Manager

---

## Estrutura do Projeto

```
browser-task-automation/
├── core/
│   ├── ferramentas.py        # Conexão, logging, verificação de ambiente
│   ├── web_paths.py          # Seletores web ofuscados
│   ├── web_paths.sample.py   # Estrutura de exemplo dos seletores
│   ├── primeira_pagina.py    # Interações da primeira página
│   └── segunda_pagina.py     # Interações da segunda página
├── input/
│   ├── url.txt               # URL alvo (não versionado)
│   └── tabelas_a_processar/  # Planilhas a processar (não versionadas)
├── output/                   # Logs e cache de progresso (não versionado)
├── encode_selector.sample.py # Como gerar seletores ofuscados
└── main.py
```

---

## Como usar

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Copie o `encode_selector.sample.py`, preencha com seus seletores, rode e cole o output no `web_paths.py`
4. Adicione a URL alvo em `input/url.txt`
5. Coloque as planilhas em `input/tabelas_a_processar/`
6. Execute:
```bash
python main.py
```

---

## Observações

- Desenvolvido e utilizado ativamente em ambiente de trabalho real
- O sistema-alvo é mantido intencionalmente privado a pedido da equipe
- A ofuscação dos seletores é uma decisão arquitetural consciente, não um contorno
