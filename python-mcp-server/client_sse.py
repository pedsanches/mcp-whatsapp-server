#!/usr/bin/env python3
"""
Cliente MCP para servidor WhatsApp - Versão SSE
"""

import asyncio
import os
import json
import aiohttp
from dotenv import load_dotenv
from mcp import ClientSession, types
from mcp.client.http import http_client

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

async def main():
    print(f"Iniciando cliente MCP WhatsApp (SSE) - Conectando a {MCP_SERVER_URL}...")
    
    # Conectar ao servidor via HTTP/SSE
    async with aiohttp.ClientSession() as http_session:
        async with http_client(http_session, MCP_SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                # Inicializar a conexão
                print("Inicializando sessão com o servidor...")
                await session.initialize()
                
                # Registrar para receber notificações
                @session.on_notification("notifications/message")
                async def handle_notification(notification):
                    level = notification.get("level", "info")
                    data = notification.get("data", "")
                    print(f"[{level.upper()}] {data}")
                
                # Listar ferramentas disponíveis
                print("\n=== Ferramentas disponíveis ===")
                tools = await session.list_tools()
                
                # Processar ferramentas corretamente
                for tool in tools:
                    # Verificar o formato de retorno e processar adequadamente
                    if hasattr(tool, 'name') and hasattr(tool, 'description'):
                        # Formato de objeto
                        print(f"- {tool.name}: {tool.description}")
                    elif isinstance(tool, (list, tuple)) and len(tool) >= 2:
                        # Formato de tupla/lista
                        print(f"- {tool[0]}: {tool[1]}")
                    elif isinstance(tool, dict) and 'name' in tool and 'description' in tool:
                        # Formato de dicionário
                        print(f"- {tool['name']}: {tool['description']}")
                    else:
                        # Outro formato
                        print(f"- {tool}")
                
                # Listar recursos disponíveis
                print("\n=== Recursos disponíveis ===")
                resources = await session.list_resources()
                
                # Processar recursos corretamente
                for resource in resources:
                    # Verificar o formato de retorno e processar adequadamente
                    if hasattr(resource, 'name') and hasattr(resource, 'description'):
                        # Formato de objeto
                        print(f"- {resource.name}: {resource.description}")
                    elif isinstance(resource, (list, tuple)) and len(resource) >= 2:
                        # Formato de tupla/lista
                        print(f"- {resource[0]}: {resource[1]}")
                    elif isinstance(resource, dict) and 'name' in resource and 'description' in resource:
                        # Formato de dicionário
                        print(f"- {resource['name']}: {resource['description']}")
                    else:
                        # Outro formato
                        print(f"- {resource}")
                
                # Listar prompts disponíveis (apenas na versão SSE)
                print("\n=== Prompts disponíveis ===")
                try:
                    prompts = await session.list_prompts()
                    for prompt in prompts:
                        if hasattr(prompt, 'name') and hasattr(prompt, 'description'):
                            # Formato de objeto
                            print(f"- {prompt.name}: {prompt.description}")
                            if hasattr(prompt, 'arguments') and prompt.arguments:
                                print("  Argumentos:")
                                for arg in prompt.arguments:
                                    req = "(Obrigatório)" if arg.required else "(Opcional)"
                                    print(f"    - {arg.name}: {arg.description} {req}")
                        elif isinstance(prompt, dict) and 'name' in prompt and 'description' in prompt:
                            # Formato de dicionário
                            print(f"- {prompt['name']}: {prompt['description']}")
                            if 'arguments' in prompt and prompt['arguments']:
                                print("  Argumentos:")
                                for arg in prompt['arguments']:
                                    req_status = "(Obrigatório)" if arg.get('required', False) else "(Opcional)"
                                    print(f"    - {arg.get('name')}: {arg.get('description')} {req_status}")
                        else:
                            # Outro formato
                            print(f"- {prompt}")
                except Exception as e:
                    print(f"Erro ao listar prompts: {e}")
                
                # Ler o recurso de configuração
                print("\n=== Lendo recurso de configuração ===")
                try:
                    config_content, mime_type = await session.read_resource("waha://configuracao")
                    print(f"Configuração: {config_content}")
                    if isinstance(config_content, str) and config_content.startswith('{'):
                        # Tentar formatar como JSON se for uma string JSON
                        try:
                            config_json = json.loads(config_content)
                            print("Configuração formatada:")
                            for key, value in config_json.items():
                                print(f"  {key}: {value}")
                        except json.JSONDecodeError:
                            pass
                except Exception as e:
                    print(f"Erro ao ler recurso: {e}")
                
                # Usar um prompt (se disponível)
                try:
                    print("\n=== Usando prompt de mensagem ===")
                    numero = input("Digite o número de telefone (ex: 5511999999999): ")
                    mensagem = input("Digite a mensagem: ")
                    
                    prompt_result = await session.get_prompt(
                        "mensagem_whatsapp", 
                        arguments={"numero": numero, "corpo": mensagem}
                    )
                    
                    print("\nPrompt gerado:")
                    # Verificar o formato do prompt
                    if hasattr(prompt_result, 'messages'):
                        for msg in prompt_result.messages:
                            if hasattr(msg, 'content') and hasattr(msg, 'role'):
                                if isinstance(msg.content, types.TextContent):
                                    print(f"[{msg.role}] {msg.content.text}")
                                else:
                                    print(f"[{msg.role}] Conteúdo não textual")
                            elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                                print(f"[{msg['role']}] {msg['content'].get('text', 'Conteúdo não textual')}")
                            else:
                                print(f"Mensagem: {msg}")
                    elif isinstance(prompt_result, dict) and 'messages' in prompt_result:
                        for msg in prompt_result['messages']:
                            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                                print(f"[{msg['role']}] {msg['content'].get('text', 'Conteúdo não textual')}")
                            else:
                                print(f"Mensagem: {msg}")
                    else:
                        print(f"Resultado do prompt: {prompt_result}")
                except Exception as e:
                    print(f"Erro ao usar prompt: {e}")
                
                # Enviar uma mensagem de teste
                print("\n=== Envio de mensagem ===")
                try:
                    resultado = await session.call_tool(
                        "enviar_mensagem_whatsapp",
                        arguments={"numero": numero, "mensagem": mensagem}
                    )
                    print(f"Resultado: {resultado}")
                    if isinstance(resultado, dict):
                        print("Detalhes:")
                        for key, value in resultado.items():
                            print(f"  {key}: {value}")
                except Exception as e:
                    print(f"Erro ao chamar ferramenta: {e}")
                
                # Aguardar um momento para receber as notificações
                print("\nAguardando notificações (5 segundos)...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main()) 