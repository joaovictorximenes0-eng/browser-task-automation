# Recuperação de sessão não está bom ainda. Ele identifica a sessão mas insere o link para o login de qualquer forma
# Colocar uma barra de progresso fora do terminal
# Colocar um timer após cada registro para dar tempo do servidor respirar e receber a requisição
# Comando terminal: google-chrome --remote-debugging-port=9222 --user-data-dir="~/ChromeProfile"
import sys
import os
import time
import pandas as pd
import csv  
from datetime import datetime 
from core.ferramentas import configurar_logger, verificar_ambiente, listar_planilhas, conectar, normalizar
from core.primeira_pagina import (
    acessar_frame_principal, obter_painel_de_tarefas, expandir_filtros,
    preencher_id_registro, executar_pesquisa, acessar_item_na_lista
)
from core.segunda_pagina import (
    abrir_detalhes_registros, clicar_icone_categoria, inserir_nome_categoria,
    marcar_checkbox_categoria, confirmar_acao_final, fechar_modal_clicando_fora
)

# CONSTANTES
ARQUIVO_CACHE = "output/registros_processados.csv" 
ARQUIVO_CATEGORIA_NOME = "input/categorias.txt"
MODO_APENAS_PRIMEIRA_COLUNA = True
logger = configurar_logger()

# --- FUNÇÕES AUXILIARES ---
def ler_registros_ods(caminho):
    try:
        if caminho.endswith('.ods'):
            df = pd.read_excel(caminho, engine='odf')
        else:
            df = pd.read_excel(caminho) 

        if MODO_APENAS_PRIMEIRA_COLUNA:
            coluna_dados = df.iloc[:, 0].dropna().astype(str)
            return [p.strip() for p in coluna_dados if p.strip()]
        else:
            todos = df.values.flatten()
            return [str(p).strip() for p in todos if str(p).strip() != 'nan' and str(p).strip()]
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {caminho}: {e}")
        return []

def carregar_parametros_categoria(caminho_arquivo, lista_categorias=ARQUIVO_CATEGORIA_NOME):
    try:
        with open(lista_categorias, "r", encoding="utf-8") as f:
            categorias_disponiveis = [l.strip() for l in f if l.strip()]
    except:
        logger.critical("Erro: 'input/categorias.txt' não encontrado.")
        sys.exit(1)

    nome_arquivo = normalizar(os.path.basename(caminho_arquivo))
    melhor_match, maior_score = None, 0

    for categoria in categorias_disponiveis:
        score = sum(1 for p in normalizar(categoria).split() if p in nome_arquivo)
        if score > maior_score:
            maior_score = score
            melhor_match = categoria

    if melhor_match: return melhor_match
    logger.error(f"Não achei categoria correspondente para o arquivo: {os.path.basename(caminho_arquivo)}")
    return None

# --- NOVA LÓGICA DE CACHE (CSV) ---
def carregar_cache_concluidos():
    cache = set()
    if not os.path.exists(ARQUIVO_CACHE):
        return cache
    
    try:
        with open(ARQUIVO_CACHE, mode='r', encoding='utf-8', newline='') as f:
            leitor = csv.reader(f)
            next(leitor, None) # Pula o cabeçalho
            for linha in leitor:
                if len(linha) >= 2:
                    # Reconstrói a chave "Registro|Categoria" para usar no set
                    chave = f"{linha[0]}|{linha[1]}"
                    cache.add(chave)
    except Exception as e:
        logger.error(f"Erro ao ler cache CSV: {e}")
    
    return cache

def registrar_sucesso(registro, categoria):
    arquivo_existe = os.path.exists(ARQUIVO_CACHE)
    
    try:
        with open(ARQUIVO_CACHE, mode='a', encoding='utf-8', newline='') as f:
            escritor = csv.writer(f)
            
            # Se é arquivo novo, cria o cabeçalho das colunas
            if not arquivo_existe:
                escritor.writerow(["ID_Registro", "Categoria_Atribuida", "Data_Hora_Conclusao"])
            
            # Salva os dados
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            escritor.writerow([registro, categoria, data_hora])
            
    except Exception as e:
        logger.error(f"Erro ao salvar no CSV: {e}")

# --- EXECUÇÃO PRINCIPAL ---
def main():
    # 1. Verificação inicial
    if not verificar_ambiente(): return

    # 2. Conecta 
    try:
        driver = conectar()
    except Exception as e:
        logger.critical(f"Falha ao conectar: {e}")
        return

    # 3. Lista arquivos
    arquivos_para_processar = listar_planilhas()
    logger.info(f"--- INÍCIO DO LOTE ---")
    logger.info(f"Encontrados {len(arquivos_para_processar)} arquivos na pasta 'tabelas'.")

    # 4. Loop pelos arquivos
    for arquivo_atual in arquivos_para_processar:
        nome_arquivo = os.path.basename(arquivo_atual)
        logger.info(f"\n{'='*40}")
        logger.info(f"ARQUIVO: {nome_arquivo}")
        logger.info(f"{'='*40}")

        categoria_alvo = carregar_parametros_categoria(arquivo_atual)
        if not categoria_alvo: 
            logger.warning(f"Pulando arquivo {nome_arquivo} (Categoria não identificada).")
            continue 

        registros = ler_registros_ods(arquivo_atual)
        cache_concluidos = carregar_cache_concluidos() 

        # --- ESTATÍSTICAS DE RECUPERAÇÃO ---
        total_registros = len(registros)
        feitos_neste_arquivo = 0
        
        # Lógica de contagem adaptada
        for p in registros:
            chave_verificacao = f"{p}|{categoria_alvo}"
            if chave_verificacao in cache_concluidos:
                feitos_neste_arquivo += 1
        
        restantes = total_registros - feitos_neste_arquivo
        logger.info(f"Categoria: {categoria_alvo}")
        logger.info(f"Status: {feitos_neste_arquivo} já feitos | {restantes} restantes | {total_registros} total")
        time.sleep(1) 

        # 5. Loop pelos registros
        for id_registro in registros:
            chave = f"{id_registro}|{categoria_alvo}"
            
            if chave in cache_concluidos:
                logger.info(f"-> [PULANDO] {id_registro} (Já consta no CSV)")
                continue

            logger.info(f"Wait... Processando: {id_registro}")
            fase = 1
            
            try:
                acessar_frame_principal(driver)
                bloco = obter_painel_de_tarefas(driver)
                expandir_filtros(bloco)
                preencher_id_registro(driver, bloco, id_registro)
                executar_pesquisa(bloco)
                time.sleep(0.5)

                acessar_item_na_lista(bloco)
                abrir_detalhes_registros(driver)

                fase = 2
                clicar_icone_categoria(driver)
                time.sleep(0.5)
                inserir_nome_categoria(driver, categoria_alvo)
                marcar_checkbox_categoria(driver)
                confirmar_acao_final(driver)
                time.sleep(2)
                # Salva no CSV
                registrar_sucesso(id_registro, categoria_alvo)
                cache_concluidos.add(chave) 

                fechar_modal_clicando_fora(driver)
                time.sleep(0.5)
                driver.execute_script("window.history.back()")
                driver.switch_to.default_content()
                logger.info(f"[OK] {id_registro} finalizado com sucesso.")

            except Exception as e:
                logger.error(f"[ERRO] Falha na Fase {fase} (ID: {id_registro}): {e}")
                
                # Tentativa de recuperação de crash
                try:
                    if fase == 2:
                        driver.execute_script("window.history.back()")
                        time.sleep(2)
                    driver.switch_to.default_content()
                    logger.warning("Tentando refresh para destravar...")
                    driver.refresh()
                    time.sleep(4)
                except:
                    pass

    logger.info("\n=== BATCH FINALIZADO COMPLETAMENTE ===")
    logger.info("O navegador permanecerá aberto para verificações futuras.")

if __name__ == "__main__":
    main()