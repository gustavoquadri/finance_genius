import json
import re
import time
from base64 import b64encode
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

BASE = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://sistemaswebb3-listados.b3.com.br/",
    "Origin": "https://sistemaswebb3-listados.b3.com.br",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

def _b64(d: dict) -> str:
    return b64encode(json.dumps(d, ensure_ascii=False).encode("utf-8")).decode("utf-8")

def _ticker_root(ticker: str) -> str:
    # PETR4 -> PETR ; TAEE11 -> TAEE
    return "".join(re.findall(r"[A-Za-z]+", ticker.upper()))

def _date_key(ev: Dict[str, Any]) -> datetime:
    s = ev.get("paymentDate") or ev.get("exDividendDate") or ev.get("exDate") or ""
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:
        return datetime.min

def _request_with_retry(url: str, headers: Dict[str, str], tries: int = 3, timeout: int = 20) -> requests.Response:
    last_exc = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            # alguns 520/502 vêm com HTML; forçamos erro p/ tentar de novo
            r.raise_for_status()
            # se não for JSON, tenta de novo
            try:
                _ = r.json()
            except Exception:
                raise requests.HTTPError("Non-JSON response", response=r)
            return r
        except Exception as e:
            last_exc = e
            # backoff simples
            time.sleep(0.8 * (i + 1))
    if last_exc:
        raise last_exc

def _pick_company_blob(payload: Any, root: str) -> Optional[Dict[str, Any]]:
    """
    A resposta da B3 pode vir como:
      - dict com as chaves diretamente (tem 'cashDividends'), ou
      - list[dict] com várias companhias; precisamos escolher a certa.
    """
    if isinstance(payload, dict):
        return payload

    if isinstance(payload, list):
        # tenta bater por issuingCompany / tradingName / acrônimo que contém a raiz
        root_up = root.upper()
        best = None
        for item in payload:
            if not isinstance(item, dict):
                continue
            ic = (item.get("issuingCompany") or item.get("issuingCompanyAcronym") or item.get("company") or "")
            tn = (item.get("tradingName") or "")
            # prioridade: match exato por raiz ou prefixo
            if ic.upper().startswith(root_up) or root_up in ic.upper():
                return item
            if tn and tn.upper().startswith(root_up):
                best = best or item
        return best
    return None

def get_cash_dividends_fast(ticker: str) -> List[Dict[str, Any]]:
    """
    Pega proventos (dividendos/JCP) a partir de GetListedSupplementCompany,
    lidando com respostas em list/dict e variações de chaves.
    """
    root = _ticker_root(ticker)
    params = {"issuingCompany": root, "language": "pt-br"}
    url = f"{BASE}/GetListedSupplementCompany/{_b64(params)}"

    r = _request_with_retry(url, HEADERS, tries=4, timeout=25)
    payload = r.json()

    company = _pick_company_blob(payload, root)
    if not company:
        raise ValueError(f"Companhia não encontrada para raiz '{root}'. Payload inesperado da B3.")

    # Alguns retornos aninham os dados em 'results' ou 'company'
    if "results" in company and isinstance(company["results"], list) and company["results"]:
        company = company["results"][0]
    if "company" in company and isinstance(company["company"], dict):
        company = company["company"]

    cash = (company.get("cashDividends")
            or company.get("CashDividends")
            or company.get("dividends")  # raríssimo, mas já vi
            or [])

    # Se ainda estiver vazio, pode ser que o array esteja direto no payload (quando payload é dict)
    if not cash and isinstance(payload, dict):
        cash = payload.get("cashDividends") or []

    if not isinstance(cash, list):
        # às vezes vem como dict com 'items'
        cash = cash.get("items", []) if isinstance(cash, dict) else []

    out: List[Dict[str, Any]] = []
    for ev in cash:
        if not isinstance(ev, dict):
            continue
        out.append({
            "ticker": ticker.upper(),
            "tipo": (ev.get("type") or ev.get("eventType") or "").strip(),
            "data_ex": ev.get("exDividendDate") or ev.get("exDate"),
            "data_com": ev.get("recordDate") or ev.get("recordingDate"),
            "pagamento": ev.get("paymentDate"),
            "valor_por_acao": ev.get("rate") or ev.get("value"),
            "moeda": ev.get("currency"),
            "observacao": ev.get("remarks") or ev.get("note") or ev.get("obs"),
        })

    out.sort(key=_date_key)
    return out

# Exemplo rápido:
eventos = get_cash_dividends_fast("BBSE3")
for e in eventos[:10]:
    print(e)
