#!/usr/bin/env python3
"""
Servidor MCP para integração com Waha API (WhatsApp)
Versão stdio para uso com Claude Desktop
"""

import os
import asyncio
import requests
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
WAHA_API_URL = os.getenv("WAHA_API_URL", "http://localhost:3000")
SESSION_ID = os.getenv("WAHA_SESSION_ID", "default")
CONTATOS_FILE = os.getenv("CONTATOS_FILE", os.path.join(os.path.dirname(__file__), "contatos.json"))

# Criar o servidor MCP
mcp = FastMCP("WhatsApp Server")

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
            return {
                "status": "error",
                "mensagem": "Nenhuma sessão WhatsApp encontrada. Verifique se o Waha está autenticado."
            }
        
        # Verificar se alguma sessão existe - muitas vezes a API funciona mesmo se a sessão
        # não estiver marcada como "CONNECTED" explicitamente
        # Esse é um comportamento comum em algumas versões da API Waha
        return {
            "status": "success",
            "mensagem": f"Waha API está respondendo com {len(sessions)} sessões",
            "sessions": sessions
        }
    except Exception as e:
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
            return {
                "sucesso": False,
                "erro": "Formato de número inválido",
                "mensagem": f"O número '{numero}' deve conter apenas dígitos (ex: 5511999999999)"
            }
        
        # Verificar se a API está acessível
        status = verificar_status_waha()
        if status.get("status") == "error":
            return {
                "sucesso": False,
                "erro": "API Waha não acessível",
                "mensagem": status.get("mensagem")
            }
        
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
            return {
                "sucesso": True,
                "resposta": response.json(),
                "mensagem": f"Mensagem enviada com sucesso para {numero}"
            }
        
        # Se chegou aqui, temos um erro real
        return {
            "sucesso": False,
            "erro": f"Erro na API Waha: {response.status_code} - {response.text}",
            "mensagem": f"Falha ao enviar mensagem para {numero}: Código {response.status_code}"
        }
    except requests.RequestException as e:
        # Erro específico de requisição HTTP
        return {
            "sucesso": False,
            "erro": str(e),
            "mensagem": f"Falha ao enviar mensagem para {numero}: {str(e)}",
            "solucao": "Verifique se a API Waha está em execução em " + WAHA_API_URL
        }
    except Exception as e:
        # Outros erros
        return {
            "sucesso": False,
            "erro": str(e),
            "mensagem": f"Falha ao enviar mensagem para {numero}: {str(e)}"
        }

def carregar_contatos():
    """
    Carrega os contatos do arquivo JSON
    """
    try:
        if os.path.exists(CONTATOS_FILE):
            with open(CONTATOS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("contatos", {})
        else:
            print(f"Arquivo de contatos não encontrado: {CONTATOS_FILE}")
            return {}
    except Exception as e:
        print(f"Erro ao carregar contatos: {str(e)}")
        return {}

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

@mcp.resource("waha://contatos")
def contatos_waha():
    """Lista de contatos mapeados por nome para números de telefone"""
    contatos = carregar_contatos()
    return {
        "uri": "waha://contatos",
        "name": "Contatos WhatsApp",
        "mimeType": "application/json",
        "description": "Mapeamento de nomes para números de telefone no WhatsApp",
        "data": contatos
    }

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

@mcp.tool()
def enviar_mensagem_por_nome(nome: str, mensagem: str):
    """
    Envia uma mensagem de texto via WhatsApp para um contato pelo nome
    
    Args:
        nome: Nome do contato cadastrado no sistema
        mensagem: Conteúdo da mensagem a ser enviada
    
    Returns:
        dict: Resultado da operação
    """
    contatos = carregar_contatos()
    if nome in contatos:
        return enviar_mensagem_waha(contatos[nome], mensagem)
    else:
        return {
            "sucesso": False,
            "erro": "Contato não encontrado",
            "mensagem": f"O contato '{nome}' não está cadastrado no sistema"
        }

if __name__ == "__main__":
    # Verificar status do Waha ao iniciar
    status = verificar_status_waha()
    print(f"Status do WhatsApp: {status['mensagem']}")
    
    print("Servidor MCP Waha iniciado. Aguardando comandos...")
    mcp.run() 