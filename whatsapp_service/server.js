import http from 'node:http'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
} from '@whiskeysockets/baileys'
import dotenv from 'dotenv'
import pino from 'pino'
import qrcode from 'qrcode-terminal'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')

dotenv.config({ path: path.join(projectRoot, '.env') })

const HOST = process.env.BAILEYS_SERVICE_HOST || '127.0.0.1'
const PORT = Number.parseInt(process.env.BAILEYS_SERVICE_PORT || '3001', 10)
const WEBHOOK_URL = process.env.WHATSAPP_WEBHOOK_URL || 'http://127.0.0.1:3002/webhook/whatsapp'
const authConfigurado = process.env.BAILEYS_AUTH_DIR || 'whatsapp_service/auth_info'
const AUTH_DIR = path.isAbsolute(authConfigurado)
  ? authConfigurado
  : path.resolve(projectRoot, authConfigurado)
const LOG_LEVEL = process.env.BAILEYS_LOG_LEVEL || 'silent'
const baileysLogger = pino({ level: LOG_LEVEL })
const INBOUND_ENABLED = ['1', 'true', 'yes', 'sim'].includes(
  String(process.env.WHATSAPP_INBOUND_ENABLED || 'false').trim().toLowerCase(),
)
const INBOUND_ALLOWED_PHONE = String(process.env.WHATSAPP_INBOUND_ALLOWED_PHONE || '').replace(/\D/g, '')
const SERVICO_INICIADO_EM_MS = Date.now()

let sock = null
let conectado = false
let conectando = false
let estadoConexao = 'iniciando'
let timerReconexao = null

function responderJson(res, status, dados) {
  const corpo = JSON.stringify(dados)
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(corpo),
  })
  res.end(corpo)
}

function normalizarTelefone(telefone) {
  const digitos = String(telefone ?? '').replace(/\D/g, '')
  if (digitos.length < 10 || digitos.length > 15) {
    throw new Error('Telefone inválido. Informe somente um número com DDI e DDD.')
  }
  return digitos
}

function telefoneParaJid(telefone) {
  return `${normalizarTelefone(telefone)}@s.whatsapp.net`
}

async function resolverDestinatario(telefone) {
  if (!sock) {
    throw new Error('WhatsApp ainda não está conectado.')
  }

  const numero = normalizarTelefone(telefone)
  const jidConsultado = telefoneParaJid(numero)
  const resultados = await sock.onWhatsApp(jidConsultado)
  const resultado = Array.isArray(resultados) ? resultados[0] : null

  if (!resultado?.exists || !resultado?.jid) {
    throw new Error('O número informado não foi reconhecido como uma conta válida do WhatsApp.')
  }

  return {
    numero,
    jid: resultado.jid,
  }
}

function codigoDesconexao(erro) {
  return erro?.output?.statusCode ?? erro?.statusCode ?? null
}

function agendarReconexao() {
  if (timerReconexao) return

  timerReconexao = setTimeout(() => {
    timerReconexao = null
    iniciarWhatsApp().catch((erro) => {
      console.error('[ERRO] Falha ao reconectar ao WhatsApp:', erro.message)
      agendarReconexao()
    })
  }, 3000)
}

function desembrulharMensagem(conteudo) {
  let atual = conteudo

  for (let i = 0; i < 4 && atual; i += 1) {
    if (atual.ephemeralMessage?.message) {
      atual = atual.ephemeralMessage.message
      continue
    }
    if (atual.viewOnceMessageV2?.message) {
      atual = atual.viewOnceMessageV2.message
      continue
    }
    if (atual.viewOnceMessage?.message) {
      atual = atual.viewOnceMessage.message
      continue
    }
    break
  }

  return atual || {}
}

function extrairTextoMensagem(mensagem) {
  const conteudo = desembrulharMensagem(mensagem?.message)
  return String(
    conteudo.conversation
      ?? conteudo.extendedTextMessage?.text
      ?? conteudo.imageMessage?.caption
      ?? conteudo.videoMessage?.caption
      ?? ''
  ).trim()
}

function extrairMensagemCitadaId(mensagem) {
  const conteudo = desembrulharMensagem(mensagem?.message)
  return conteudo.extendedTextMessage?.contextInfo?.stanzaId ?? null
}

function extrairTelefoneMensagem(mensagem) {
  const chave = mensagem?.key || {}
  const candidatos = [chave.remoteJidAlt, chave.remoteJid].filter(Boolean)
  const jid = candidatos.find((valor) => String(valor).endsWith('@s.whatsapp.net'))

  if (!jid) return null

  const usuario = String(jid).split('@')[0].split(':')[0]
  const digitos = usuario.replace(/\D/g, '')
  return digitos.length >= 10 && digitos.length <= 15 ? digitos : null
}

function ehComandoRenovar(texto) {
  const normalizado = String(texto || '')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9À-Ú ]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  return ['RENOVAR', 'RENOVAR EMPRESTIMO', 'RENOVAR EMPRÉSTIMO'].includes(normalizado)
}

function timestampMensagemMs(mensagem) {
  const valor = mensagem?.messageTimestamp
  if (typeof valor === 'number') return valor * 1000
  if (typeof valor === 'bigint') return Number(valor) * 1000
  if (valor && typeof valor.toNumber === 'function') return valor.toNumber() * 1000

  const numero = Number(valor)
  return Number.isFinite(numero) ? numero * 1000 : null
}

function mensagemEhRecente(mensagem) {
  const timestamp = timestampMensagemMs(mensagem)
  if (!timestamp) return false

  const agora = Date.now()
  return timestamp >= SERVICO_INICIADO_EM_MS - 30_000 && timestamp <= agora + 60_000
}

async function encaminharMensagemAoWebhook(mensagem) {
  if (!INBOUND_ENABLED) return
  if (!mensagem?.key || mensagem.key.fromMe) return
  if (!mensagemEhRecente(mensagem)) return

  const telefone = extrairTelefoneMensagem(mensagem)
  const texto = extrairTextoMensagem(mensagem)
  const messageId = String(mensagem.key.id || '').trim()
  const quotedMessageId = extrairMensagemCitadaId(mensagem)

  if (!telefone || !texto || !messageId) return

  if (INBOUND_ALLOWED_PHONE && telefone !== INBOUND_ALLOWED_PHONE) {
    return
  }

  // Conversas comuns não pertencem ao bot. Só encaminhamos RENOVAR ou respostas.
  if (!ehComandoRenovar(texto) && !quotedMessageId) {
    return
  }

  const payload = {
    phone: telefone,
    message: texto,
    message_id: messageId,
    quoted_message_id: quotedMessageId,
  }

  try {
    const resposta = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15000),
    })

    let dados = {}
    try {
      dados = await resposta.json()
    } catch {
      dados = {}
    }

    if (!resposta.ok || !dados.ok) {
      console.warn(`[AVISO] Webhook recusou mensagem recebida: ${dados.error || `HTTP ${resposta.status}`}`)
      return
    }

    const status = dados.result?.status || 'processada'
    console.log(`[INFO] Mensagem de renovação recebida e processada pelo webhook: ${status}`)
  } catch (erro) {
    console.warn(`[AVISO] Não foi possível encaminhar mensagem ao webhook Python: ${erro.message}`)
  }
}

async function iniciarWhatsApp() {
  if (conectando) return
  conectando = true
  estadoConexao = 'conectando'

  try {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR)

    const novoSock = makeWASocket({
      auth: state,
      logger: baileysLogger,
      markOnlineOnConnect: false,
      syncFullHistory: false,
    })

    sock = novoSock
    novoSock.ev.on('creds.update', saveCreds)

    novoSock.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect, qr } = update

      if (qr) {
        estadoConexao = 'aguardando_qr'
        console.log('\n[INFO] Escaneie o QR Code abaixo no WhatsApp para vincular o BiblioAvisa:\n')
        qrcode.generate(qr, { small: true })
      }

      if (connection === 'open') {
        conectado = true
        estadoConexao = 'conectado'
        console.log('[OK] WhatsApp conectado pelo Baileys.')
      }

      if (connection === 'close') {
        conectado = false
        const statusCode = codigoDesconexao(lastDisconnect?.error)
        const saiuDaConta = statusCode === DisconnectReason.loggedOut

        if (saiuDaConta) {
          estadoConexao = 'desvinculado'
          console.error('[ERRO] A sessão do WhatsApp foi desvinculada. Apague a pasta de sessão local e vincule novamente.')
          return
        }

        estadoConexao = 'desconectado'
        console.warn('[AVISO] Conexão com WhatsApp encerrada. Tentando reconectar...')
        agendarReconexao()
      }
    })

    novoSock.ev.on('messages.upsert', ({ messages, type }) => {
      if (!INBOUND_ENABLED || type !== 'notify' || !Array.isArray(messages)) return

      for (const mensagem of messages) {
        encaminharMensagemAoWebhook(mensagem).catch((erro) => {
          console.warn('[AVISO] Falha ao tratar mensagem de renovação:', erro.message)
        })
      }
    })
  } finally {
    conectando = false
  }
}

async function lerJson(req) {
  const partes = []
  let tamanho = 0

  for await (const parte of req) {
    tamanho += parte.length
    if (tamanho > 64 * 1024) {
      throw new Error('Corpo da requisição muito grande.')
    }
    partes.push(parte)
  }

  const texto = Buffer.concat(partes).toString('utf8')
  if (!texto.trim()) return {}

  try {
    return JSON.parse(texto)
  } catch {
    throw new Error('JSON inválido.')
  }
}

const servidor = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    responderJson(res, 200, {
      ok: true,
      provider: 'baileys',
      connected: conectado,
      state: estadoConexao,
      webhook_url: WEBHOOK_URL,
      inbound_enabled: INBOUND_ENABLED,
      inbound_allowlist_active: Boolean(INBOUND_ALLOWED_PHONE),
    })
    return
  }

  if (req.method === 'POST' && req.url === '/check') {
    if (!conectado || !sock) {
      responderJson(res, 503, {
        ok: false,
        error: 'WhatsApp ainda não está conectado.',
        state: estadoConexao,
      })
      return
    }

    try {
      const dados = await lerJson(req)
      const destino = await resolverDestinatario(dados.phone)

      responderJson(res, 200, {
        ok: true,
        provider: 'baileys',
        exists: true,
        jid: destino.jid,
      })
    } catch (erro) {
      responderJson(res, 400, {
        ok: false,
        exists: false,
        error: erro.message,
      })
    }
    return
  }

  if (req.method === 'POST' && req.url === '/send') {
    if (!conectado || !sock) {
      responderJson(res, 503, {
        ok: false,
        error: 'WhatsApp ainda não está conectado.',
        state: estadoConexao,
      })
      return
    }

    try {
      const dados = await lerJson(req)
      const mensagem = String(dados.message ?? '').trim()

      if (!mensagem) {
        responderJson(res, 400, { ok: false, error: 'A mensagem não pode ficar vazia.' })
        return
      }

      const destino = await resolverDestinatario(dados.phone)
      const resultado = await sock.sendMessage(destino.jid, { text: mensagem })

      responderJson(res, 200, {
        ok: true,
        provider: 'baileys',
        accepted: true,
        delivered: false,
        recipient_jid: destino.jid,
        message_id: resultado?.key?.id ?? null,
        note: 'O retorno de sendMessage confirma aceitação pelo Baileys, não entrega ao destinatário.',
      })
    } catch (erro) {
      console.error('[ERRO] Falha ao enviar mensagem:', erro.message)
      responderJson(res, 500, { ok: false, error: erro.message })
    }
    return
  }

  responderJson(res, 404, { ok: false, error: 'Rota não encontrada.' })
})

servidor.listen(PORT, HOST, () => {
  console.log(`[OK] Serviço Baileys local em http://${HOST}:${PORT}`)
  console.log(`[INFO] Sessão local: ${AUTH_DIR}`)
  console.log(`[INFO] Log interno do Baileys: ${LOG_LEVEL}`)
  console.log(`[INFO] Webhook de respostas: ${WEBHOOK_URL}`)
  console.log(`[INFO] Recebimento automático: ${INBOUND_ENABLED ? 'ATIVADO' : 'DESATIVADO'}`)
  if (INBOUND_ENABLED) {
    console.log(`[INFO] Filtro de telefone para entrada: ${INBOUND_ALLOWED_PHONE ? 'ATIVO' : 'NÃO CONFIGURADO'}`)
  }
  iniciarWhatsApp().catch((erro) => {
    estadoConexao = 'erro'
    console.error('[ERRO] Não foi possível iniciar o Baileys:', erro.message)
    agendarReconexao()
  })
})

process.on('SIGINT', () => {
  console.log('\n[INFO] Encerrando serviço Baileys...')
  servidor.close(() => process.exit(0))
})
