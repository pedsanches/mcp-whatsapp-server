#!/usr/bin/env python3
"""
Servidor MCP para integração com Waha API (WhatsApp)
Versão SSE (Server-Sent Events) com servidor web
"""

import os
import logging
import uuid
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
WAHA_API_URL = os.getenv("WAHA_API_URL", "http://localhost:3000")
MCP_PORT = int(os.getenv("MCP_PORT", 8000))
SESSION_ID = os.getenv("WAHA_SESSION_ID", "default")

# Criar o servidor MCP
mcp = FastMCP("WhatsApp Server SSE")

def verificar_status_waha():
    """
    Verifica se a API Waha está online e autenticada no WhatsApp
    """
    try:
        # Verificar se a API está online
        response = requests.get(f"{WAHA_API_URL}/api/sessions")
        response.raise_for_status()
        
        # Verificar se há uma sessão ativa
        sessions = response.json()
        if not sessions:
            logger.warning("Nenhuma sessão WhatsApp encontrada")
            return {
                "status": "error",
                "mensagem": "Nenhuma sessão WhatsApp encontrada. Verifique se o Waha está autenticado."
            }
        
        # Verificar se alguma sessão existe - muitas vezes a API funciona mesmo se a sessão
        # não estiver marcada como "CONNECTED" explicitamente
        logger.info(f"Waha API está respondendo com {len(sessions)} sessões")
        return {
            "status": "success",
            "mensagem": f"Waha API está respondendo com {len(sessions)} sessões",
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status do Waha: {str(e)}")
        return {
            "status": "error",
            "mensagem": f"Erro ao verificar status do Waha: {str(e)}"
        }

def enviar_mensagem_waha(numero, mensagem):
    """
    Envia uma mensagem via WhatsApp usando a API Waha
    """
    try:
        # Verificar formato do número de telefone
        if not numero.isdigit():
            error_msg = f"Formato de número inválido: '{numero}'"
            logger.error(error_msg)
            mcp.notify("error", error_msg)
            return {
                "status": "error",
                "error": "Formato de número inválido",
                "message": f"O número '{numero}' deve conter apenas dígitos (ex: 5511999999999)"
            }
        
        # Verificar se a API está acessível
        status = verificar_status_waha()
        if status.get("status") == "error":
            error_msg = f"API Waha não acessível: {status.get('mensagem')}"
            logger.error(error_msg)
            mcp.notify("error", error_msg)
            return {
                "status": "error",
                "error": "API Waha não acessível",
                "message": status.get("mensagem")
            }
        
        logger.info(f"Enviando mensagem para {numero}")
        
        # Enviar mensagem com parâmetros completos
        response = requests.post(
            f"{WAHA_API_URL}/api/sendText",
            json={
                "chatId": f"{numero}@c.us", 
                "reply_to": None, 
                "text": mensagem, 
                "linkPreview": True, 
                "linkPreviewHighQuality": False, 
                "session": SESSION_ID
            },
            timeout=10
        )
        
        # Verificar resposta - códigos 200 e 201 são ambos considerados sucesso
        # 200 = OK, 201 = Created (mensagem criada com sucesso)
        if response.status_code in [200, 201]:
            success_msg = f"Mensagem enviada com sucesso para {numero}"
            logger.info(success_msg)
            
            # Enviar notificação
            mcp.notify("info", success_msg)
            
            return {
                "status": "success",
                "data": response.json(),
                "message": success_msg
            }
        
        # Se chegou aqui, temos um erro real
        error_msg = f"Erro na API Waha: {response.status_code} - {response.text}"
        logger.error(error_msg)
        mcp.notify("error", error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": f"Falha ao enviar mensagem para {numero}: Código {response.status_code}"
        }
    except requests.RequestException as e:
        # Erro específico de requisição HTTP
        error_msg = f"Falha ao enviar mensagem para {numero}: {str(e)}"
        logger.error(error_msg)
        mcp.notify("error", error_msg)
        return {
            "status": "error",
            "error": str(e),
            "message": error_msg,
            "solucao": "Verifique se a API Waha está em execução em " + WAHA_API_URL
        }
    except Exception as e:
        # Outros erros
        error_msg = f"Falha ao enviar mensagem para {numero}: {str(e)}"
        logger.error(error_msg)
        mcp.notify("error", error_msg)
        return {
            "status": "error",
            "error": str(e),
            "message": error_msg
        }

@mcp.resource("waha://configuracao")
def configuracao_waha():
    """Configurações para a API Waha"""
    return {
        "apiUrl": WAHA_API_URL,
        "sessionId": SESSION_ID
    }

@mcp.resource("waha://status")
def status_waha():
    """Status da conexão com o WhatsApp"""
    return verificar_status_waha()

@mcp.tool()
def verificar_conexao_whatsapp():
    """
    Verifica se o WhatsApp está conectado através da API Waha
    
    Returns:
        dict: Status da conexão WhatsApp
    """
    return verificar_status_waha()

@mcp.tool()
def enviar_mensagem_whatsapp(numero: str, mensagem: str):
    """
    Envia uma mensagem de texto via WhatsApp usando a API Waha
    
    Args:
        numero: Número de telefone completo com código do país (sem '+' ou espaços, ex: 5511999999999)
        mensagem: Conteúdo da mensagem a ser enviada
    
    Returns:
        dict: Resultado da operação
    """
    return enviar_mensagem_waha(numero, mensagem)

@mcp.prompt()
def mensagem_whatsapp(numero: str, corpo: str):
    """
    Cria um template de mensagem para WhatsApp
    
    Args:
        numero: Número de telefone (formato: 5511999999999)
        corpo: Conteúdo da mensagem
    """
    return f"""
Por favor, envie a seguinte mensagem no WhatsApp:

Número: {numero}
Mensagem: {corpo}

Utilize a ferramenta enviar_mensagem_whatsapp.
"""

if __name__ == "__main__":
    # Verificar status do Waha ao iniciar
    status = verificar_status_waha()
    logger.info(f"Status do WhatsApp: {status['mensagem']}")
    
    # Configurar middleware CORS para permitir solicitações de qualquer origem
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )
    ]
    
    # Criar aplicação Starlette com middleware e montagem do servidor SSE
    app = Starlette(
        middleware=middleware,
        routes=[
            Mount('/', app=mcp.sse_app()),
        ]
    )
    
    logger.info(f"Iniciando servidor MCP SSE na porta {MCP_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info") 