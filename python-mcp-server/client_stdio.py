#!/usr/bin/env python3
"""
Cliente MCP para servidor WhatsApp - Versão stdio
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Carregar variáveis de ambiente
load_dotenv()

async def main():
    print("Iniciando cliente MCP WhatsApp (stdio)...")
    
    # Parâmetros para servidor stdio
    server_params = StdioServerParameters(
        command="python",  # Executável
        args=["server.py"],  # Script do servidor
        env=None,  # Variáveis de ambiente serão herdadas
    )
    
    # Conectar ao servidor via stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Inicializar a conexão
            print("Inicializando sessão com o servidor...")
            await session.initialize()
            
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
            
            # Enviar uma mensagem de teste (solicitando input do usuário)
            print("\n=== Envio de mensagem ===")
            numero = input("Digite o número de telefone (ex: 5511999999999): ")
            mensagem = input("Digite a mensagem: ")
            
            # Chamar a ferramenta
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

if __name__ == "__main__":
    asyncio.run(main()) 