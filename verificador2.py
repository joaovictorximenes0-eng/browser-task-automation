import os
import time
import sys
import pandas as pd
import re
import shutil
import runpy
import unicodedata

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# --- IMPORTAÇÕES INTERNAS ---
try:
    from core.extracao import extrair_todos_processos 
    from core.primeira_pagina import acessar_frame_principal
    from core.ferramentas import conectar
except ImportError as e:
    print(f"[ERRO FATAL] Falha ao importar módulo interno: {e}")
    sys.exit()

# ==========================================
# --- CONFIGURAÇÕES E CONSTANTES ---
# ==========================================

ARQUIVO_INPUT = 'input/nome.txt'
ARQUIVO_ESPELHO_SISTEMA = "output/relatorio_processos.csv" 
ARQUIVO_CACHE_APP = "output/processos_concluidos.csv"      
PASTA_ENTRADA_TOTAL = "input/tabelas_a_processar"
PASTA_SAIDA_DELTA = "input/temp_delta_run"
COLUNA_PROCESSO_ORIGINAL = "Processo" 

# ==========================================
# --- FUNÇÕES DE LIMPEZA E DEDUÇÃO ---
# ==========================================

def limpar_numero(valor):
    """Deixa só números para comparação (remove ., -, / e espaços)."""
    if pd.isna(valor) or not valor or str(valor).lower() == 'nan': 
        return ""
    return re.sub(r'\D', '', str(valor))

def normalizar(texto):
    """Remove acentos, espaços extras e deixa minúsculo."""
    if pd.isna(texto): return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto

def carregar_nome_etiqueta(caminho_arquivo):
    """
    Cruza o nome do arquivo da tabela com a lista de etiquetas em input/nome.txt.
    Retorna a etiqueta com a maior correspondência (score) de palavras.
    """
    try:
        with open(ARQUIVO_INPUT, "r", encoding="utf-8") as f:
            nomes_possiveis = [l.strip() for l in f if l.strip()]
    except Exception as e:
        print(f"[ERRO FATAL] 'input/nome.txt' não encontrado ou inacessível: {e}")
        sys.exit(1)

    nome_arquivo = normalizar(os.path.basename(caminho_arquivo))
    melhor, maior_score = None, 0

    for nome in nomes_possiveis:
        score = sum(1 for p in normalizar(nome).split() if p in nome_arquivo)
        if score > maior_score:
            maior_score = score
            melhor = nome

    if melhor: 
        return melhor
        
    print(f"      [AVISO] Nenhuma etiqueta do txt combinou com o arquivo: {os.path.basename(caminho_arquivo)}")
    return None

# ==========================================
# --- ETAPAS DE EXECUÇÃO ---
# ==========================================

def navegar_para_etiqueta_e_extrair(driver, nome_alvo):
    print(f"      Navegando no PJe para buscar: '{nome_alvo}'...")
    acessar_frame_principal(driver)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "i.fa-tags, i.fa-bookmark"))
    ).click()
    time.sleep(2)

    campo = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Pesquisar'], input.search-query"))
    )
    campo.clear()
    campo.send_keys(nome_alvo)
    campo.send_keys(u'\ue007') # Aperta Enter
    time.sleep(3)

    seletor = f"//span[contains(text(), '{nome_alvo}')] | //div[contains(text(), '{nome_alvo}')]"
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, seletor))).click()
    
    print("      Aguardando carregamento da lista (Timeout: 60s)...")
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "divListaProcessos")))
    
    try:
        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CLASS_NAME, "ajax-loader")))
    except:
        pass 
    
    time.sleep(2) 
    print("      [OK] Lista carregada! Iniciando extração...")
    extrair_todos_processos(driver, nome_alvo)

def sincronizar_e_limpar_cache(nome_etiqueta_alvo):
    print("      Sincronizando Histórico (App) vs Realidade (PJe)...")
    
    if not os.path.exists(ARQUIVO_CACHE_APP) or not os.path.exists(ARQUIVO_ESPELHO_SISTEMA):
        return

    df_sistema = pd.read_csv(ARQUIVO_ESPELHO_SISTEMA, sep=None, engine='python')
    realidade_set = set(df_sistema.iloc[:, 0].apply(limpar_numero))

    df_cache = pd.read_csv(ARQUIVO_CACHE_APP)
    etiqueta_norm_alvo = normalizar(nome_etiqueta_alvo)

    validos, discrepancias = [], []

    for _, row in df_cache.iterrows():
        proc_limpo = limpar_numero(row.get('Numero_Processo', ''))
        etiq_norm = normalizar(row.get('Nome_Etiqueta', ''))

        if etiq_norm == etiqueta_norm_alvo:
            if proc_limpo in realidade_set:
                validos.append(row)
            else:
                discrepancias.append(row.get('Numero_Processo', 'Desconhecido'))
        else:
            validos.append(row)

    if discrepancias:
        print(f"      [ALERTA] Removendo {len(discrepancias)} falsos positivos do histórico!")
        pd.DataFrame(validos).to_csv(ARQUIVO_CACHE_APP, index=False)
    else:
        print("      [OK] Histórico está em perfeita sintonia.")

def gerar_delta_por_arquivo(arquivo):
    print(f"      Calculando Delta (pendências)...")
    
    if not os.path.exists(ARQUIVO_ESPELHO_SISTEMA):
        lista_no_sistema = set()
    else:
        df_sistema = pd.read_csv(ARQUIVO_ESPELHO_SISTEMA, sep=None, engine='python')
        lista_no_sistema = set(df_sistema.iloc[:, 0].apply(limpar_numero))

    caminho_full = os.path.join(PASTA_ENTRADA_TOTAL, arquivo)
    df_total = pd.read_excel(caminho_full, engine='odf' if arquivo.endswith('.ods') else None)
    
    col_ref = df_total[COLUNA_PROCESSO_ORIGINAL] if COLUNA_PROCESSO_ORIGINAL in df_total.columns else df_total.iloc[:, 0]
    df_faltantes = df_total[~col_ref.apply(limpar_numero).isin(lista_no_sistema)].copy()

    qtd = len(df_faltantes)
    if qtd > 0:
        caminho_saida = os.path.join(PASTA_SAIDA_DELTA, f"DELTA_{arquivo}")
        df_faltantes.to_excel(caminho_saida, index=False)
        print(f"      [DELTA] Restam {qtd} processos a fazer nesta tabela.")
    else:
        print(f"      [OK] Tabela '{arquivo}' está 100% concluída no sistema!")
        
    return qtd

# ==========================================
# --- ORQUESTRAÇÃO PRINCIPAL ---
# ==========================================

if __name__ == "__main__":
    arquivos = [f for f in os.listdir(PASTA_ENTRADA_TOTAL) if f.endswith(('.xlsx', '.ods'))]
    if not arquivos:
        sys.exit(f"[ERRO] Nenhuma planilha encontrada na pasta '{PASTA_ENTRADA_TOTAL}'.")

    # Limpa a pasta Delta de execuções anteriores logo no início
    if os.path.exists(PASTA_SAIDA_DELTA):
        shutil.rmtree(PASTA_SAIDA_DELTA)
    os.makedirs(PASTA_SAIDA_DELTA)

    driver = conectar()
    total_pendentes_gerais = 0

    # LOOP PRINCIPAL: Passa por cada arquivo da pasta
    for arquivo in arquivos:
        # AGORA USA A SUA FUNÇÃO BASEADA NO NOME.TXT
        nome_etiqueta = carregar_nome_etiqueta(arquivo)
        
        if not nome_etiqueta:
            print(f"\n[AVISO] Ignorando '{arquivo}': Nenhuma etiqueta no nome.txt combinou.")
            continue

        print(f"\n{'='*50}")
        print(f" TABELA: {arquivo}")
        print(f" ETIQUETA: {nome_etiqueta}")
        print(f"{'='*50}")

        # Apaga o relatório do loop anterior para não misturar dados
        if os.path.exists(ARQUIVO_ESPELHO_SISTEMA):
            os.remove(ARQUIVO_ESPELHO_SISTEMA)

        try:
            # Refresh garante que o PJe volta pra tela inicial entre um loop e outro
            driver.switch_to.default_content()
            driver.refresh()
            time.sleep(4)
            
            # 1. Extração
            navegar_para_etiqueta_e_extrair(driver, nome_etiqueta)
        except Exception as e:
            print(f"      [ERRO NA EXTRAÇÃO] Pulando esta tabela: {e}")
            continue

        # 2. Sincronização (Purge)
        sincronizar_e_limpar_cache(nome_etiqueta)

        # 3. Delta
        total_pendentes_gerais += gerar_delta_por_arquivo(arquivo)


    # --- FASE FINAL: RODAR O APP.PY ---
    if total_pendentes_gerais > 0:
        print("\n>>> Preparando terreno e injetando o app.py...")
        try:
            driver.switch_to.default_content()
            driver.refresh()
            time.sleep(4)
        except: pass

        from core import ferramentas
        ferramentas.TABELAS_A_PROCESSAR = PASTA_SAIDA_DELTA
        
        print("\n" + "="*50)
        print(f" INICIANDO RECUPERAÇÃO GERAL ({total_pendentes_gerais} PROCESSOS) ")
        print("="*50 + "\n")
        
        runpy.run_path("app.py", run_name="__main__")
        
    else:
        print("\n>>> SUCESSO ABSOLUTO: Todas as tabelas da pasta estão 100% sincronizadas!")

    # Limpeza do rastro do verificador
    if os.path.exists(ARQUIVO_ESPELHO_SISTEMA):
        os.remove(ARQUIVO_ESPELHO_SISTEMA)