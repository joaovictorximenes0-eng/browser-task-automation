import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from core.ferramentas import configurar_logger, obter_elemento, WebPaths

logger = configurar_logger()

def abrir_detalhes_registros(driver):
    logger.debug("Procurando botão de selecionar processo...")
    time.sleep(1.2)

    btn = obter_elemento(driver, "BTN_PROCESS", tempo=20)

    time.sleep(0.4)
    btn.click()
    logger.info("[OK] Botão SELECIONAR PROCESSO clicado com sucesso!")

def clicar_icone_categoria(driver):
    logger.debug("Procurando botão 'Vincular etiqueta'...")
    try:
        btn = obter_elemento(driver, "BTN_LINK", tempo=10)
        try:
            btn.click()
        except:
            driver.execute_script("arguments[0].click();", btn)

        logger.info("[OK] Modal de etiquetas aberto (Botão ícone clicado).")
        return True

    except Exception as e:
        logger.error(f"[X] Erro ao localizar/clicar no botão 'Vincular etiqueta': {e}", exc_info=True)
        raise

def inserir_nome_categoria(driver, nome, wait_time=5):
    logger.info(f"Preenchendo etiqueta: '{nome}'...")

    # 1. Localizar o campo (Usa o dicionário via obter_elemento)
    campo = obter_elemento(driver, "INPUT_SEARCH", tempo=wait_time)
    
    # 2. Limpeza
    campo.click()
    campo.clear()
    time.sleep(0.2)

    # 3. Digitação
    for ch in nome:
        campo.send_keys(ch)
        time.sleep(0.05) 

    # 4. Disparar eventos
    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", campo)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", campo)
    
    logger.debug("[OK] Texto digitado e eventos JS disparados.")
    time.sleep(1.0) 

    # 5. Clicar na sugestão (MODULARIZADO)
    nome_upper = nome.upper()
    
    # Recupera a lista de strings cruas do dicionário
    templates = WebPaths.SUGGESTION_TEMPLATES
    
    sugestao_clicada = False
    
    for tpl in templates:
        # Aqui injetamos o nome dinamicamente no XPath que veio do arquivo de ferramentas
        xpath_formatado = tpl.format(nome_upper)
        
        try:
            # Mantemos o WebDriverWait direto aqui pois é um loop de tentativa
            # e 'obter_elemento' espera uma chave de dicionário, não um Xpath bruto.
            elem = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xpath_formatado))
            )
            
            try:
                elem.click()
            except:
                driver.execute_script("arguments[0].click();", elem)
            
            logger.info("[OK] Sugestão (dropdown) selecionada.")
            sugestao_clicada = True
            break
        except TimeoutException:
            continue
    
    if not sugestao_clicada:
        logger.warning("[!] Aviso: Sugestão da etiqueta não clicada. Verifique se o nome está exato.")
        
    time.sleep(0.5)
    return True

def marcar_checkbox_categoria(driver, timeout=10):
    logger.debug("Iniciando busca do checkbox da etiqueta...")
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            btn = WebDriverWait(driver, 0.5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, WebPaths.CHK_LABEL)))    
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)     
            try:
                btn.click()
            except WebDriverException:
                driver.execute_script("arguments[0].click();", btn)

            logger.info("[OK] Checkbox marcado.")
            return
        except (StaleElementReferenceException, TimeoutException):
            continue
        except Exception:
            time.sleep(0.1)
            continue

    logger.error(f"[X] Timeout: Não foi possível marcar checkbox após {timeout}s.")
    raise Exception(f"Falha ao marcar checkbox após {timeout}s.")

def confirmar_acao_final(driver, timeout=5):
    logger.debug("Procurando botão final 'Vincular etiqueta'...")

    try:
        # AGORA SIM: Usamos o helper modularizado com XPATH
        btn = obter_elemento(driver, "BTN_CONFIRM_LINK", by=By.XPATH, tempo=timeout)
        
        try:
            btn.click()
        except:
            driver.execute_script("arguments[0].click();", btn)
            
        logger.info("[OK] Vinculação confirmada (Botão Final).")
        return True

    except Exception as e:
        logger.error(f"[X] Erro ao clicar no botão final: {e}", exc_info=True)
        raise

def fechar_modal_clicando_fora(driver, x=20, y=20):
    logger.debug(f"Fechando modal (clique em {x},{y})...")
    html = driver.find_element(By.TAG_NAME, "html")
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(html, x, y).click().perform()
    logger.info("[OK] Modal fechado.")