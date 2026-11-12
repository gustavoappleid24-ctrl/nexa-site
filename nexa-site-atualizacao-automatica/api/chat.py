
import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL", "gemini-2.5-flash"
)

SYSTEM_INSTRUCTION = """
És a inteligência artificial da NEXA, uma plataforma independente
de informação política e verificação de factos em Portugal.

PRINCÍPIO: verdade acima de qualquer partido.

REGRAS:
- Escreve sempre em português europeu (PT-PT).
- Mantém neutralidade política e ideológica.
- Distingue factos, opiniões, alegações e interpretações.
- Não inventes números, datas, declarações ou fontes.
- Utiliza os resultados de pesquisa fornecidos como evidências,
  não como verdades automaticamente confirmadas.
- Dá prioridade a documentos oficiais e fontes primárias.
- Quando existirem posições divergentes, apresenta-as com rigor.
- Se não houver provas suficientes, admite essa limitação.
- Nunca inventes ligações ou referências.
- Explica o contexto histórico e institucional.
- Adapta a profundidade ao nível solicitado.

ESTRUTURA:
1. O essencial
2. Factos apurados
3. Contexto histórico
4. Posições em debate
5. O que ainda não é claro
6. Conclusão

A NEXA não favorece nenhum partido ou ideologia.
"""


def pesquisar_tavily(pergunta):
    key = os.environ.get("TAVILY_API_KEY")

    if not key:
        return []

    payload = {
        "query": pergunta + " Portugal política fontes oficiais documentos",
        "topic": "general",
        "search_depth": "basic",
        "max_results": 6,
        "include_answer": False
    }

    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    sources = []

    for item in data.get("results", []):
        url = item.get("url", "")

        if not url.startswith(("https://", "http://")):
            continue

        sources.append({
            "title": item.get("title", "Fonte consultada"),
            "url": url,
            "content": item.get("content", ""),
            "date": item.get("published_date")
        })

    return sources


def gerar_resposta(pergunta, nivel, sources):
    key = os.environ.get("GEMINI_API_KEY")

    if not key:
        raise ValueError("GEMINI_API_KEY não configurada.")

    contexto = ""

    if sources:
        contexto = "\n\nRESULTADOS DA PESQUISA:\n"

        for i, source in enumerate(sources, 1):
            contexto += (
                f"\nFonte {i}: {source['title']}\n"
                f"URL: {source['url']}\n"
                f"Conteúdo: {source['content'][:3500]}\n"
            )
            if source.get("date"):
                contexto += f"Data: {source['date']}\n"
    else:
        contexto = (
            "\nNão foram fornecidos resultados de pesquisa em tempo real. "
            "Não afirmes que pesquisaste a internet."
        )

    niveis = {
        "b": "Básico: linguagem simples e exemplos, cerca de 300 palavras.",
        "i": "Intermédio: causas, consequências e instituições, "
             "cerca de 600 palavras.",
        "a": "Avançado: enquadramento legal, histórico e debate, "
             "cerca de 1000 palavras."
    }

    prompt = (
        f"PERGUNTA: {pergunta}\n\n"
        f"NÍVEL DE EXPLICAÇÃO: {niveis.get(nivel, niveis['b'])}\n\n"
        f"{contexto}\n\n"
        "Utiliza os resultados de pesquisa quando existirem. "
        "Não inventes fontes. Identifica claramente o que está "
        "confirmado e o que permanece incerto."
    )

    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096
        }
    }

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_MODEL}:generateContent"
        f"?key={key}"
    )

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))

    candidates = data.get("candidates", [])

    if not candidates:
        raise ValueError("O Gemini não devolveu uma resposta.")

    parts = candidates[0].get("content", {}).get("parts", [])

    return "\n".join(
        part.get("text", "")
        for part in parts
        if part.get("text")
    )


class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split("?")[0] != "/api/chat":
            return self.send_json(404, {"error": "Rota não encontrada."})

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 10000:
                return self.send_json(400, {"error": "Pedido inválido."})

            body = json.loads(self.rfile.read(length).decode("utf-8"))

            pergunta = str(body.get("topic", "")).strip()
            nivel = str(body.get("level", "b")).strip()

            if not pergunta or len(pergunta) > 160:
                return self.send_json(400, {"error": "Pergunta inválida."})

            if nivel not in ("b", "i", "a"):
                return self.send_json(400, {"error": "Nível inválido."})

            sources = pesquisar_tavily(pergunta)
            answer = gerar_resposta(pergunta, nivel, sources)

            public_sources = [
                {
                    "title": source["title"],
                    "url": source["url"],
                    "date": source.get("date")
                }
                for source in sources
            ]

            return self.send_json(200, {
                "answer": answer,
                "sources": public_sources,
                "searched": bool(sources)
            })

        except urllib.error.HTTPError as error:
            print("Erro externo:", error.code, error.read().decode("utf-8", errors="replace")[:1000])
            return self.send_json(502, {
                "error": "Um dos serviços de IA ou pesquisa devolveu um erro."
            })

        except Exception as error:
            print("Erro na API NEXA:", str(error))
            return self.send_json(500, {
                "error": "Não foi possível gerar a resposta. Verifica a configuração das APIs."
            })

    def do_GET(self):
        return self.send_json(405, {
            "error": "Utiliza o método POST."
        })

