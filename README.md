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

## How it works

1. `main.py` reads the spreadsheets from the input folder and identifies the target category based on the filename
2. For each record, it checks the CSV cache — skipping anything already processed
3. Opens the browser (or reconnects to an existing session), navigates to the target URL and waits for login if needed
4. For each pending record: searches by ID, opens the details, assigns the category and confirms
5. Every success is written to the cache immediately — so an interruption loses at most one record

The page interaction logic is split into two modules: `primeira_pagina.py` handles search and navigation, `segunda_pagina.py` handles the assignment flow.

---

## Can I use this for my own system?

The architecture is reusable — progress cache, session management, logging and selector obfuscation all work independently of the target system.

However, `primeira_pagina.py` and `segunda_pagina.py` contain scraping logic that is specific to the original web interface. To adapt this project to a different system, those two modules would need to be rewritten from scratch through your own scraping work. The effort is the same regardless of which system you target — that part cannot be generalized.

If that still fits your use case, feel free to fork.

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

## Notes

- Developed and actively used in a real work environment
- The target system is intentionally kept private at the team's request
- Selector obfuscation is a conscious architectural decision, not a workaround

---
---

# Automação de Tarefas do Navegador

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

## Como funciona

1. `main.py` lê as planilhas da pasta de input e identifica a categoria alvo com base no nome do arquivo
2. Para cada registro, verifica o cache CSV — pulando o que já foi processado
3. Abre o navegador (ou reconecta a uma sessão existente), navega até a URL alvo e aguarda o login se necessário
4. Para cada registro pendente: pesquisa pelo ID, abre os detalhes, atribui a categoria e confirma
5. Cada sucesso é gravado no cache imediatamente — uma interrupção perde no máximo um registro

A lógica de interação com as páginas está dividida em dois módulos: `primeira_pagina.py` cuida da pesquisa e navegação, `segunda_pagina.py` cuida do fluxo de atribuição.

---

## Posso usar para o meu sistema?

A arquitetura é reutilizável — cache de progresso, gerenciamento de sessão, logging e ofuscação de seletores funcionam de forma independente do sistema-alvo.

Porém, `primeira_pagina.py` e `segunda_pagina.py` contêm lógica de scraping específica para a interface web original. Para adaptar o projeto a um sistema diferente, esses dois módulos precisariam ser reescritos do zero com o seu próprio trabalho de scraping. O esforço é o mesmo independente do sistema — essa parte não pode ser generalizada.

Se ainda assim faz sentido para o seu caso, fique à vontade para fazer um fork.

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

## Observações

- Desenvolvido e utilizado ativamente em ambiente de trabalho real
- O sistema-alvo é mantido intencionalmente privado a pedido da equipe
- A ofuscação dos seletores é uma decisão arquitetural consciente, não um contorno
