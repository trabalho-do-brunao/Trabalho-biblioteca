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
const authConfigurado = process.env.BAILEYS_AUTH_DIR || 'whatsapp_service/auth_info'
const AUTH_DIR = path.isAbsolute(authConfigurado)
  ? authConfigurado
  : path.resolve(projectRoot, authConfigurado)
const LOG_LEVEL = process.env.BAILEYS_LOG_LEVEL || 'silent'
const baileysLogger = pino({ level: LOG_LEVEL })

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
