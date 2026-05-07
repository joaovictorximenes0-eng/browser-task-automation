import pandas as pd
import re
import time
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging

logger = logging.getLogger('RoboPJe')

def extrair_todos_processos(driver, nome_etiqueta):
    """
    Função Mestra:
    1. Extrai a página 1.
    2. Verifica se existe página 2, 3... e clica nelas.
    3. Repete até não haver mais páginas.
    """
    pagina_atual = 1
    total_extraido = 0
    
    while True:
        logger.info(f"--- Processando PÁGINA {pagina_atual} ---")
        
        # 1. Raspa a página atual
        qtd_na_pagina = processar_pagina_atual(driver, nome_etiqueta)
        total_extraido += qtd_na_pagina
        
        # 2. Tenta ir para a próxima
        if tentar_avancar_pagina(driver, pagina_atual):
            pagina_atual += 1
            # Pequena pausa técnica para garantir estabilidade do Ajax
            time.sleep(2) 
        else:
            logger.info("Fim da paginação. Não há mais páginas seguintes.")
            break
            
    logger.info(f"=== EXTRAÇÃO CONCLUÍDA. Total de {total_extraido} processos salvos. ===")

def processar_pagina_atual(driver, nome_etiqueta):
    """
    Lê os cards visíveis APENAS na tela atual e salva no CSV.
    """
    dados = []
    try:
        # Aguarda a lista aparecer (spinner sumir)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "divListaProcessos"))
        )
        
        # Pega todos os cards visíveis
        cards = driver.find_elements(By.TAG_NAME, "processo-datalist-card")
        
        if not cards:
            logger.warning("Nenhum card encontrado nesta página.")
            return 0

        for card in cards:
            try:
                # Busca o número dentro do card
                elemento_texto = card.find_element(By.CSS_SELECTOR, "span.tarefa-numero-processo")
                texto_bruto = elemento_texto.text.strip()
                
                # Regex para limpar "AlvJud..." e "COPIADO"
                match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", texto_bruto)
                numero_limpo = match.group(0) if match else texto_bruto.replace("COPIADO", "").strip()

                dados.append({
                    "processo_no_sistema": numero_limpo,
                    "Nome_Etiqueta": nome_etiqueta,
                    "Data_Hora_Conclusao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception:
                continue # Se falhar um card, pula pro próximo
        
        # Salva o lote dessa página
        if dados:
            salvar_em_csv(dados)
            return len(dados)
        return 0

    except Exception as e:
        logger.error(f"Erro ao ler página: {e}")
        return 0

def tentar_avancar_pagina(driver, numero_pagina_atual):
    """
    Busca o botão da próxima página (atual + 1) e clica nele.
    Retorna True se conseguiu, False se acabou.
    """
    proxima_pagina = numero_pagina_atual + 1
    logger.debug(f"Procurando botão para página {proxima_pagina}...")

    try:
        # Estratégia: Procurar dentro do paginador um link <a> que tenha o texto exato do número
        # O xpath procura um link <a> que contenha o texto '2', '3', etc.
        xpath_botao = f"//span[contains(@class, 'ui-paginator-pages')]//a[normalize-space()='{proxima_pagina}']"
        
        botao_proxima = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath_botao))
        )
        
        # Antes de clicar, vamos pegar o primeiro processo da lista atual
        # para comparar depois e garantir que a página mudou
        try:
            primeiro_processo_antigo = driver.find_element(By.TAG_NAME, "processo-datalist-card").text
        except:
            primeiro_processo_antigo = ""

        # Clica via JavaScript para evitar erros de elemento encoberto
        driver.execute_script("arguments[0].click();", botao_proxima)
        
        logger.info(f"Clicado na página {proxima_pagina}. Aguardando carregamento...")
        
        # Espera Inteligente: Espera até que o primeiro processo da lista SEJA DIFERENTE do antigo
        # ou espera o spinner de carregamento sumir
        aguardar_mudanca_de_pagina(driver, primeiro_processo_antigo)
        
        return True

    except (TimeoutException, NoSuchElementException):
        return False

def aguardar_mudanca_de_pagina(driver, texto_referencia):
    """Espera a tabela atualizar os dados."""
    try:
        # Espera até 10 segundos para que o primeiro card mude de texto
        WebDriverWait(driver, 10).until(
            lambda d: obter_texto_primeiro_card(d) != texto_referencia
        )
    except TimeoutException:
        logger.warning("O tempo de espera da paginação excedeu, mas vou tentar continuar.")

def obter_texto_primeiro_card(driver):
    try:
        return driver.find_element(By.TAG_NAME, "processo-datalist-card").text
    except:
        return ""

def salvar_em_csv(dados):
    arquivo_saida = "output/relatorio_processos.csv"
    df = pd.DataFrame(dados)
    colunas = ["processo_no_sistema", "Nome_Etiqueta", "Data_Hora_Conclusao"]
    
    # Modo 'a' (append) para não apagar o que gravou na página 1 quando for gravar a 2
    header = not os.path.exists(arquivo_saida)
    df[colunas].to_csv(arquivo_saida, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')