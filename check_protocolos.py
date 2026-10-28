import os
import requests
from playwright.sync_api import sync_playwright

WEBAPP_URL = os.environ.get("WEBAPP_URL")

def extrair_aprova_digital(page, url, usuario, senha):
    protocolos = []
    try:
        page.goto(url)
        page.fill('input[type="email"]', usuario)
        page.fill('input[type="password"]', senha)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        rows = page.query_selector_all("tr.linha-processo")
        for row in rows:
            protocolo = row.query_selector(".col-protocolo").inner_text().strip() if row.query_selector(".col-protocolo") else "N/A"
            analista = row.query_selector(".col-analista").inner_text().strip() if row.query_selector(".col-analista") else "Não atribuído"
            status = row.query_selector(".col-status").inner_text().strip() if row.query_selector(".col-status") else "N/A"
            exigencia = row.query_selector(".col-exigencia").inner_text().strip() if row.query_selector(".col-exigencia") else "Nenhuma"
            
            protocolos.append({
                "protocolo": protocolo,
                "analista": analista,
                "status": status,
                "exigencia": exigencia
            })
    except Exception as e:
        print(f"Erro no Aprova Digital ({url}): {e}")
    return protocolos

def extrair_atende_net(page, url, usuario, senha):
    protocolos = []
    try:
        page.goto(url)
        page.wait_for_selector('input[name="txtLogin"]', timeout=10000)
        page.fill('input[name="txtLogin"]', usuario)
        page.fill('input[name="txtSenha"]', senha)
        page.click('.btn-entrar')
        page.wait_for_load_state("networkidle")
        
        rows = page.query_selector_all(".grid-row-processo")
        for row in rows:
            protocolo = row.query_selector(".col-num-processo").inner_text().strip() if row.query_selector(".col-num-processo") else "N/A"
            analista = row.query_selector(".col-responsavel").inner_text().strip() if row.query_selector(".col-responsavel") else "Pendente"
            status = row.query_selector(".col-situacao").inner_text().strip() if row.query_selector(".col-situacao") else "N/A"
            exigencia = row.query_selector(".col-parecer").inner_text().strip() if row.query_selector(".col-parecer") else "Sem pendências"
            
            protocolos.append({
                "protocolo": protocolo,
                "analista": analista,
                "status": status,
                "exigencia": exigencia
            })
    except Exception as e:
        print(f"Erro no Atende.net ({url}): {e}")
    return protocolos

def main():
    res = requests.post(WEBAPP_URL, json={"action": "get_portais"})
    data = res.json()
    
    if data.get("status") != "success":
        print("Erro ao carregar portais cadastrados.")
        return
        
    portais = data.get("data", [])
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        todos_resultados = []
        
        for portal in portais:
            prefeitura = portal["prefeitura"]
            empresa = portal["empresa"]
            plataforma = portal["plataforma"]
            url = portal["url_login"]
            usuario = portal["usuario"]
            senha = portal["senha"]
            
            resultados = []
            if "APROVA" in plataforma.upper():
                resultados = extrair_aprova_digital(page, url, usuario, senha)
            elif "ATENDE" in plataforma.upper():
                resultados = extrair_atende_net(page, url, usuario, senha)
                
            for item in resultados:
                item["prefeitura"] = prefeitura
                item["empresa"] = empresa
                todos_resultados.append(item)
                
        browser.close()
        
    if todos_resultados:
        requests.post(WEBAPP_URL, json={
            "action": "update_protocolos",
            "protocolos": todos_resultados
        })
        print("Planilha atualizada com sucesso!")

if __name__ == "__main__":
    main()
