import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.ferramentas import configurar_logger, obter_elemento, WebPaths


logger = configurar_logger()

def acessar_frame_principal(driver):
    logger.debug("Aguardando carregamento do iframe principal...")
    iframe = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe")) 
    )
    driver.switch_to.frame(iframe)
    logger.info("[OK] Iframe acessado.")

def obter_painel_de_tarefas(driver): 
    logger.debug("Buscando painel 'Tarefas' no dashboard...")
    headers = driver.find_elements(By.CSS_SELECTOR, WebPaths.HEADER_DASHBOARD)
    alvo = None
    
    for h in headers:
        if h.text.strip().lower() == "tarefas":
            alvo = h
            break
            
    if not alvo: 
        logger.error("[ERRO] Painel TAREFAS não encontrado na tela.")
        raise Exception("Painel TAREFAS não encontrado!")
    
    return alvo.find_element(By.XPATH, WebPaths.HEADER_TASKS)

def expandir_filtros(bloco_tarefas):
    logger.debug("Expandindo filtros de pesquisa...")
    btn_expandir = bloco_tarefas.find_element(By.CSS_SELECTOR, WebPaths.BTN_EXPAND_FILTER)
    btn_expandir.click()
    time.sleep(1) 

def preencher_id_registro(driver, bloco_tarefas, texto):
    logger.info(f"Digitando processo: {texto}...")
    input_processo = obter_elemento(bloco_tarefas, "INPUT_RECORD_NR", tempo=20)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_processo)
    time.sleep(0.5)
    
    input_processo.clear()
    input_processo.send_keys(texto)

def executar_pesquisa(bloco_tarefas):
    logger.debug("Clicando em pesquisar...")
    btn_pesquisar = obter_elemento(bloco_tarefas, "BTN_SEARCH", tempo=20)
    btn_pesquisar.click()

def acessar_item_na_lista(bloco_tarefas):
    logger.info("Acessando o processo na lista de resultados...")
    item_tarefa = obter_elemento(bloco_tarefas, "TASK_LIST_ITEM", tempo=20)
    item_tarefa.click()