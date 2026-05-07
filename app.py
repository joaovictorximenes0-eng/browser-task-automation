# Session recovery not working well yet. It identifies the session but still inserts the login link.
# Add a progress bar outside the terminal
# Add a timer after each record to give the server time to breathe and process the request
# Terminal command: google-chrome --remote-debugging-port=9222 --user-data-dir="~/ChromeProfile"
# Connection speed could be improved
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

# CONSTANTS
CACHE_FILE = "output/processed_records.csv"
CATEGORY_FILE = "input/categories.txt"
ONLY_FIRST_COLUMN_MODE = True
logger = configurar_logger()


# Reads the ODS or XLSX file and returns a list of records. Uses global variable
def read_ods_records(path):
    try:
        if path.endswith('.ods'):
            df = pd.read_excel(path, engine='odf')
        else:
            df = pd.read_excel(path)

        if ONLY_FIRST_COLUMN_MODE:
            data_column = df.iloc[:, 0].dropna().astype(str)
            return [p.strip() for p in data_column if p.strip()]
        else:
            all_values = df.values.flatten()
            return [str(p).strip() for p in all_values if str(p).strip() != 'nan' and str(p).strip()]
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return []


# Filter: identifies category by name similarity
def load_category_params(file_path, category_list=CATEGORY_FILE):
    try:
        with open(category_list, "r", encoding="utf-8") as f:
            available_categories = [l.strip() for l in f if l.strip()]
    except Exception as e:
        logger.critical(f"Error: {category_list} not found.")
        sys.exit(1)

    file_name = normalizar(os.path.basename(file_path))
    best_match, highest_score = None, 0

    for category in available_categories:
        score = sum(1 for p in normalizar(category).split() if p in file_name)
        if score > highest_score:
            highest_score = score
            best_match = category

    if best_match:
        return best_match
    logger.error(f"No matching category found for file: {os.path.basename(file_path)}")
    return None


# Load completed tasks
def load_completed_cache():
    cache = set()
    if not os.path.exists(CACHE_FILE):
        return cache

    try:
        with open(CACHE_FILE, mode='r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    # Rebuild "Record|Category" key for the set
                    key = f"{row[0]}|{row[1]}"
                    cache.add(key)
    except Exception as e:
        logger.error(f"Error reading cache CSV: {e}")

    return cache


# Record task success for each operation
def record_success(record, category):
    file_exists = os.path.exists(CACHE_FILE)

    try:
        with open(CACHE_FILE, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # If new file, create column headers
            if not file_exists:
                writer.writerow(["Record_ID", "Assigned_Category", "Completion_DateTime"])

            # Save data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([record, category, timestamp])

    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")


def main():
    # 1. Initial check
    if not verificar_ambiente():
        return

    # 2. Connect
    try:
        driver = conectar()
    except Exception as e:
        logger.critical(f"Connection failed: {e}")
        return

    # 3. List files
    files_to_process = listar_planilhas()
    logger.info(f"--- BATCH START ---")
    logger.info(f"Found {len(files_to_process)} files in 'tabelas_a_processar' folder.")

    for current_file in files_to_process:
        file_name = os.path.basename(current_file)
        logger.info(f"\n{'='*40}")
        logger.info(f"FILE: {file_name}")
        logger.info(f"{'='*40}")

        target_category = load_category_params(current_file)
        if not target_category:
            logger.warning(f"Skipping file {file_name} (Category not identified).")
            continue

        records = read_ods_records(current_file)
        completed_cache = load_completed_cache()

        # Recovery statistics
        total_records = len(records)
        done_in_this_file = 0

        for p in records:
            check_key = f"{p}|{target_category}"
            if check_key in completed_cache:
                done_in_this_file += 1

        remaining = total_records - done_in_this_file
        logger.info(f"Category: {target_category}")
        logger.info(f"Status: {done_in_this_file} done | {remaining} remaining | {total_records} total")
        time.sleep(1)

        for record_id in records:
            key = f"{record_id}|{target_category}"

            if key in completed_cache:
                logger.info(f"-> [SKIPPING] {record_id} (Already in CSV)")
                continue

            logger.info(f"Wait... Processing: {record_id}")
            phase = 1  # State-aware recovery: handles navigation rollbacks per phase

            # HTML interaction
            try:
                acessar_frame_principal(driver)
                block = obter_painel_de_tarefas(driver)
                expandir_filtros(block)
                preencher_id_registro(driver, block, record_id)
                executar_pesquisa(block)
                time.sleep(0.5)

                acessar_item_na_lista(block)
                abrir_detalhes_registros(driver)

                phase = 2
                clicar_icone_categoria(driver)
                time.sleep(0.5)
                inserir_nome_categoria(driver, target_category)
                marcar_checkbox_categoria(driver)
                confirmar_acao_final(driver)
                time.sleep(2)

                record_success(record_id, target_category)  # Save to CSV
                completed_cache.add(key)

                fechar_modal_clicando_fora(driver)
                time.sleep(0.5)
                driver.execute_script("window.history.back()")
                driver.switch_to.default_content()
                logger.info(f"[OK] {record_id} completed successfully.")

            except Exception as e:
                logger.error(f"[ERROR] Failure in Phase {phase} (ID: {record_id}): {e}")

                # On error, move to next record
                try:
                    if phase == 2:
                        driver.execute_script("window.history.back()")
                        time.sleep(2)
                    driver.switch_to.default_content()
                    logger.warning("Attempting refresh to unblock...")
                    driver.refresh()
                    time.sleep(4)
                except:
                    pass

    logger.info("\n=== BATCH FULLY COMPLETED ===")
    logger.info("Browser will remain open for future inspection.")


if __name__ == "__main__":
    main()