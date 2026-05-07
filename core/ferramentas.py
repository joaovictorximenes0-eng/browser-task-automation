import logging
import sys
import os
import glob
import unicodedata
import re
import time
import subprocess 
import shutil
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from logging.handlers import RotatingFileHandler 
from core.web_paths import WebPaths

# --- CONFIGURAÇÕES GLOBAIS
os.environ['SE_OFFLINE'] = 'true' 
ARQUIVO_URL = "input/url.txt"
TABELAS_A_PROCESSAR = "input/tabelas_a_processar" 
LIMITE_ARQUIVO_LOG = 5 * 1024 * 1024 # 5MB
NUMERO_BACKUPS_LOG = 3




def limpar_numero(valor):
    """Remove tudo que não for dígito. Essencial para comparar números de processo."""
    if not valor or str(valor).lower() == 'nan': 
        return ""
    return re.sub(r'\D', '', str(valor))

def normalizar(texto: str) -> str:
    if not texto: return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[^a-z\s]", " ", texto)
    return texto.strip()

def configurar_logger():
    logger = logging.getLogger('RoboPJe')
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers: return logger
    
    # Correção para criar pasta logs dentro de output
    pasta_logs = os.path.join('output', 'Logs') 
    if not os.path.exists(pasta_logs):
        os.makedirs(pasta_logs)
        
    caminho_arquivo = os.path.join(pasta_logs, 'robo_trace.log')
    
    file_handler = RotatingFileHandler(
        caminho_arquivo, 
        maxBytes=LIMITE_ARQUIVO_LOG, 
        backupCount=NUMERO_BACKUPS_LOG, 
        encoding='utf-8'
    )   
    
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    console_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = configurar_logger()

def obter_opcoes_chrome(modo_debug=False):
    opts = Options()
    caminho_absoluto = os.path.abspath("output/sessao_chrome")
    if not os.path.exists(caminho_absoluto): 
        os.makedirs(caminho_absoluto)
        
    opts.add_argument(f"--user-data-dir={caminho_absoluto}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # Debug Address é usado quando conectamos num chrome JÁ aberto
    if modo_debug:
        opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    else:
        opts.add_argument("--remote-debugging-port=9222")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument("--start-maximized")
    return opts

def exibir_popup_login():
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    messagebox.showinfo("Robô PJe", "O Chrome foi aberto.\n\nSe não estiver logado, faça o LOGIN agora e depois clique em OK aqui.")
    root.destroy()

def obter_url_arquivo():
    try:
        with open(ARQUIVO_URL, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return ""

def verificar_ambiente():
    erros = []
    # Verificando pasta de input das tabelas (ajustado para o padrão do código)
    if not os.path.exists(TABELAS_A_PROCESSAR): 
        os.makedirs(TABELAS_A_PROCESSAR)
        erros.append(f"A pasta {TABELAS_A_PROCESSAR} foi criada. Coloque as planilhas lá.")

    if not os.path.exists(ARQUIVO_URL):
        # Cria arquivo vazio se não existir
        with open(ARQUIVO_URL, "w") as f: f.write("")
        erros.append(f"Arquivo '{ARQUIVO_URL}' criado vazio. Coloque o link do PJe nele.")
        
    if not os.path.exists('output'):
        os.makedirs('output')

    if not erros:
        arquivos = glob.glob(f"{TABELAS_A_PROCESSAR}/*")
        planilhas = [f for f in arquivos if f.endswith(('.xlsx', '.ods', '.csv'))]
        if not planilhas:
            erros.append(f"A pasta {TABELAS_A_PROCESSAR} está vazia.")

    if erros:
        logger.error("--- VERIFICAÇÃO INICIAL ---")
        for e in erros: logger.error(f"[!] {e}")
        return False
    return True

def listar_planilhas():
    todos = glob.glob(f"{TABELAS_A_PROCESSAR}/*")
    return [f for f in todos if f.endswith(('.xlsx', '.ods', '.csv'))]

# --- NOVA FUNÇÃO DE AUTOMATIZAÇÃO LINUX ---
def garantir_chrome_aberto_linux():
    """Verifica se o Chrome está rodando na porta 9222. Se não, abre."""
    try:
        # pgrep verifica se existe processo com esse nome
        subprocess.check_output(["pgrep", "-f", "remote-debugging-port=9222"])
        logger.info(">>> Chrome Debug já está rodando. Conectando...")
        return
    except subprocess.CalledProcessError:
        logger.info(">>> Chrome fechado. Iniciando nova instância em background...")

    caminho_perfil = os.path.abspath("output/sessao_chrome")
    
    # Tente 'google-chrome' ou 'google-chrome-stable' dependendo da sua distro
    comando = [
        "google-chrome", 
        "--remote-debugging-port=9222", 
        f"--user-data-dir={caminho_perfil}"
    ]

    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3) # Tempo para o navegador respirar
    except FileNotFoundError:
        logger.critical("ERRO: Não achei o comando 'google-chrome'. Verifique se está instalado.")
        sys.exit(1)

# --------------------------------------------------------------------------
# 4. FUNÇÃO MESTRA DE CONEXÃO (ATUALIZADA)
# --------------------------------------------------------------------------

_driver_ativo = None

def conectar(): 
    global _driver_ativo
    if _driver_ativo is not None:
        return _driver_ativo
        
    # 1. Garante que o navegador está aberto (Automação Linux)
    garantir_chrome_aberto_linux()

    # 2. Conecta no navegador aberto
    logger.info(">>> Conectando ao WebDriver...")
    try:
        opts = obter_opcoes_chrome(modo_debug=True)
        
        # --- SOLUÇÃO DE GERENCIAMENTO DE DRIVER ---
        # A) Limpa drivers antigos acumulados para salvar espaço (Opcional, mas cumpre seu requisito)
        pasta_wdm = os.path.expanduser("~/.wdm/drivers/chromedriver")
        if os.path.exists(pasta_wdm):
            shutil.rmtree(pasta_wdm)
            
        # B) Baixa o driver exato para a versão atual do seu Chrome
        caminho_driver = ChromeDriverManager().install()
        servico = Service(caminho_driver)
        
        # C) Inicia o webdriver usando o serviço gerenciado
        driver = webdriver.Chrome(service=servico, options=opts)
        # ------------------------------------------
        
        url_alvo = obter_url_arquivo()
        url_atual = driver.current_url
        
        # Lógica mais inteligente:
        precisa_navegar = False
        
        if not url_alvo:
            logger.warning("URL alvo não encontrada no arquivo url.txt")
        elif url_alvo not in url_atual:
            precisa_navegar = True
        
        if precisa_navegar:
            logger.info(f"Navegando para: {url_alvo}")
            driver.get(url_alvo)
            exibir_popup_login() 
        else:
            logger.info("Já estamos na URL correta. Verificando login...")

        logger.info(f"[OK] Conectado! Título: {driver.title}")
        _driver_ativo = driver
        return _driver_ativo

    except Exception as e:
        logger.critical(f"[ERRO FATAL] Falha ao conectar: {e}")
        raise

# Função principal para interação com HTML
def obter_elemento(driver, chave_seletor, by=By.CSS_SELECTOR, tempo=20):
    selector = getattr(WebPaths, chave_seletor, None)
    if selector is None:
        raise AttributeError(f"'{chave_seletor}' not found in WebPaths.")
        
    return WebDriverWait(driver, tempo).until(
        EC.element_to_be_clickable((by, selector))
    )