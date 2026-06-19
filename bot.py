import requests
import time
from datetime import datetime, timedelta, timezone

TOKEN = "5483533126:AAGIfCbKAXj1dzJa7kgtZKcI83a2dVBdiJA"
CHAT_ID = "-1003961010489"

URL = "https://jonbet.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"

STICKER_GREEN = "CAACAgEAAxkBAAEBuhtkFBbPbho5iUL3Cw0Zs2WBNdupaAACQgQAAnQVwEe3Q77HvZ8W3y8E"
STICKER_LOSS = "CAACAgEAAxkBAAEBuh9kFBbVKxciIe1RKvDQBeDu8WfhFAACXwIAAq-xwEfpc4OHHyAliS8E"

COR_BRANCO = 0
COR_VERDE = 1
COR_PRETO = 2

GALE_MAXIMO = 2
NIVEL_MAXIMO = 4

sinal_ativo = None
processados = set()
historico_cores = []

stats = {
    "GREEN": 0,
    "LOSS": 0
}

nivel_atual = 1
maior_gale = 0
data_stats = None

PADROES = {
    (2, 1, 1, 2): {"nome": "⚫🟢🟢⚫", "cor": 1, "texto": "🟢 VERDE"},
    (1, 2, 2, 1): {"nome": "🟢⚫⚫🟢", "cor": 2, "texto": "⚫ PRETO"},
    (2, 1, 2, 1): {"nome": "⚫🟢⚫🟢", "cor": 2, "texto": "⚫ PRETO"},
    (1, 2, 1, 2): {"nome": "🟢⚫🟢⚫", "cor": 1, "texto": "🟢 VERDE"},
    (1, 1, 2, 2): {"nome": "🟢🟢⚫⚫", "cor": 1, "texto": "🟢 VERDE"},
    (2, 2, 1, 1): {"nome": "⚫⚫🟢🟢", "cor": 2, "texto": "⚫ PRETO"},
}


def enviar(msg):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        print("Telegram:", r.status_code, r.text)
    except Exception as e:
        print("Erro Telegram:", e)


def enviar_sticker(sticker_id):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendSticker",
            data={
                "chat_id": CHAT_ID,
                "sticker": sticker_id
            },
            timeout=10
        )
        print("Sticker:", r.status_code, r.text)
    except Exception as e:
        print("Erro Sticker:", e)


def agora_br():
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=-3))
    ).replace(tzinfo=None)


def hora_br(data_api):
    return datetime.fromisoformat(
        data_api.replace("Z", "+00:00")
    ).astimezone(
        timezone(timedelta(hours=-3))
    ).replace(tzinfo=None)


def buscar_resultados():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://jonbet.bet.br/pt/games/double",
            "Origin": "https://jonbet.bet.br"
        }

        r = requests.get(URL, headers=headers, timeout=15)

        if r.status_code != 200:
            print("Erro HTTP:", r.status_code)
            return None

        return r.json()

    except Exception as e:
        print("⚠️ API falhou. Reconectando...", e)
        return None


def cor_nome(cor):
    return {
        0: "⚪ BRANCO",
        1: "🟢 VERDE",
        2: "⚫ PRETO"
    }.get(cor, str(cor))


def verificar_virada_dia():
    global data_stats, stats, nivel_atual, maior_gale, sinal_ativo, historico_cores

    hoje = agora_br().date()

    if data_stats is None:
        data_stats = hoje
        return

    if hoje != data_stats:
        stats = {
            "GREEN": 0,
            "LOSS": 0
        }

        nivel_atual = 1
        maior_gale = 0
        sinal_ativo = None
        historico_cores = []
        data_stats = hoje

        enviar("🔄 *Novo dia iniciado! Estatísticas zeradas.*")


def assertividade():
    total = stats["GREEN"] + stats["LOSS"]

    if total == 0:
        return 0

    return (stats["GREEN"] / total) * 100


def texto_stats():
    return (
        "📈 *GERAL*\n"
        f"GREEN: {stats['GREEN']:02d} | LOSS: {stats['LOSS']:02d}\n\n"
        f"SEQ: {nivel_atual:02d}/{NIVEL_MAXIMO:02d}\n"
        f"GX: {maior_gale:02d}\n\n"
        f"🎯 Assertividade: {assertividade():.2f}%"
    )


def atualizar_gx(gale):
    global maior_gale

    if gale > maior_gale:
        maior_gale = gale


def enviar_apuracao(texto, resultado_final):
    if resultado_final == "GREEN":
        enviar_sticker(STICKER_GREEN)
    elif resultado_final == "LOSS":
        enviar_sticker(STICKER_LOSS)

    msg = (
        f"{texto}\n\n"
        "📊 *APURAÇÃO*\n\n"
        f"{texto_stats()}"
    )

    print(msg)
    enviar(msg)


def enviar_sinal(sinal):
    msg = (
        "💎 *JONBET DOUBLE VIP*\n\n"
        "📊 *Estratégia:* PADRÃO\n\n"
        f"📈 *Padrão:* {sinal['padrao']}\n\n"
        "⏰ *ENTRADA:*\n"
        f"🎯 *{sinal['texto_cor']}*\n"
        f"♻️ *ATÉ G{GALE_MAXIMO}*\n\n"
        f"📌 *NÍVEL:* {nivel_atual:02d}/{NIVEL_MAXIMO:02d}"
    )

    print(msg)
    enviar(msg)


def criar_sinal_padrao(padrao_info):
    return {
        "cor": padrao_info["cor"],
        "texto_cor": padrao_info["texto"],
        "padrao": padrao_info["nome"],
        "etapa": 0,
        "max_gale": GALE_MAXIMO
    }


def verificar_padrao():
    global sinal_ativo

    if sinal_ativo is not None:
        return

    if len(historico_cores) < 4:
        return

    padrao = tuple(historico_cores[-4:])

    if padrao not in PADROES:
        return

    sinal_ativo = criar_sinal_padrao(PADROES[padrao])
    enviar_sinal(sinal_ativo)


def finalizar_green(gale):
    global sinal_ativo, nivel_atual

    stats["GREEN"] += 1
    atualizar_gx(gale)

    nivel_atual = 1

    texto = "✅ *GREEN SG*" if gale == 0 else f"✅ *GREEN G{gale}"

    enviar_apuracao(texto, "GREEN")

    sinal_ativo = None


def finalizar_loss():
    global sinal_ativo, nivel_atual

    stats["LOSS"] += 1
    atualizar_gx(GALE_MAXIMO)

    enviar_apuracao("⛔ *LOSS*", "LOSS")

    nivel_atual += 1

    if nivel_atual > NIVEL_MAXIMO:
        nivel_atual = 1
        print("🔄 Níveis reiniciados após atingir o nível máximo.")

    sinal_ativo = None


def verificar_resultado_sinal(resultado):
    global sinal_ativo

    if sinal_ativo is None:
        return

    cor_resultado = resultado["color"]

    if sinal_ativo["etapa"] == 0:
        if cor_resultado == sinal_ativo["cor"]:
            finalizar_green(0)
        else:
            sinal_ativo["etapa"] = 1
            print("⏳ Aguardando G1...")

    elif sinal_ativo["etapa"] == 1:
        if cor_resultado == sinal_ativo["cor"]:
            finalizar_green(1)
        else:
            sinal_ativo["etapa"] = 2
            print("⏳ Aguardando G2...")

    elif sinal_ativo["etapa"] == 2:
        if cor_resultado == sinal_ativo["cor"]:
            finalizar_green(2)
        else:
            finalizar_loss()


def processar_resultado(resultado, iniciar=False):
    global historico_cores

    if resultado["id"] in processados:
        return

    processados.add(resultado["id"])

    if iniciar:
        return

    verificar_resultado_sinal(resultado)

    cor = resultado["color"]

    if cor == COR_BRANCO:
        historico_cores.clear()
        print("⚪ Branco detectado. Histórico de padrões reiniciado.")
    else:
        historico_cores.append(cor)

        if len(historico_cores) > 20:
            historico_cores.pop(0)

    verificar_padrao()


enviar("✅ *Bot PADRÕES iniciado com sucesso!*")

primeira_leitura = True

while True:
    verificar_virada_dia()

    dados = buscar_resultados()

    if not dados:
        time.sleep(10)
        continue

    if primeira_leitura:
        for resultado in reversed(dados):
            processar_resultado(resultado, iniciar=True)

        primeira_leitura = False
        print("✅ Histórico inicial carregado. Aguardando padrões...")

    else:
        for resultado in reversed(dados):
            processar_resultado(resultado)

    time.sleep(1)
