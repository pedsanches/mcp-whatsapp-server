#!/usr/bin/env python3
"""
Cliente MCP para servidor WhatsApp utilizando o modelo GROQ
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("A variável de ambiente GROQ_API_KEY precisa ser configurada")

# Parâmetros para conexão com o servidor MCP via stdio
server_params = StdioServerParameters(
    command="python",  # Executável
    args=["server.py"],  # Script do servidor MCP WhatsApp
    env=None,  # Variáveis de ambiente serão herdadas
)

# Função para simular a chamada ao GROQ API
# Em um caso real, você usaria a API oficial do GROQ
async def call_groq_api(prompt_text, model="llama3-8b-8192"):
    """
    Chama a API do GROQ para gerar texto
    
    Em uma implementação real, você faria uma chamada HTTP para a API do GROQ.
    Esta é uma versão simplificada para demonstração.
    """
    print(f"\n[GROQ API] Chamando modelo {model} com prompt:")
    print(f"---\n{prompt_text}\n---")
    
    # Simular uma resposta do GROQ
    # Em uma implementação real, você faria uma requisição HTTP para a API do GROQ
    return f"[Resposta do GROQ] Processando a consulta sobre WhatsApp: '{prompt_text[:50]}...'"

# Callback para processar mensagens de amostragem (sampling)
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    """
    Processa mensagens usando o GROQ como modelo de linguagem
    """
    # Extrair o texto do prompt
    prompt_text = ""
    for msg in message.messages:
        if hasattr(msg, 'content') and hasattr(msg.content, 'text'):
            if msg.role == "user":
                prompt_text += f"Usuário: {msg.content.text}\n"
            else:
                prompt_text += f"{msg.role.capitalize()}: {msg.content.text}\n"
    
    # Chamar a API do GROQ
    response_text = await call_groq_api(prompt_text)
    
    # Retornar o resultado formatado
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text=response_text,
        ),
        model="groq:llama3-8b-8192",  # Especificar o modelo GROQ
        stopReason="endTurn",
    )

async def run():
    """
    Função principal que executa o cliente MCP com GROQ
    """
    print("Iniciando cliente MCP WhatsApp com integração GROQ...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write, sampling_callback=handle_sampling_message
        ) as session:
            # Inicializar a conexão
            print("Inicializando sessão com o servidor MCP...")
            await session.initialize()

            # Listar ferramentas disponíveis
            print("\n=== Ferramentas disponíveis ===")
            tools = await session.list_tools()
            
            # Processar e exibir ferramentas
            for tool in tools:
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    print(f"- {tool.name}: {tool.description}")
                elif isinstance(tool, (list, tuple)) and len(tool) >= 2:
                    print(f"- {tool[0]}: {tool[1]}")
                elif isinstance(tool, dict) and 'name' in tool and 'description' in tool:
                    print(f"- {tool['name']}: {tool['description']}")
                else:
                    print(f"- {tool}")

            # Listar recursos disponíveis
            print("\n=== Recursos disponíveis ===")
            resources = await session.list_resources()
            
            # Processar e exibir recursos
            for resource in resources:
                if hasattr(resource, 'name') and hasattr(resource, 'description'):
                    print(f"- {resource.name}: {resource.description}")
                elif isinstance(resource, (list, tuple)) and len(resource) >= 2:
                    print(f"- {resource[0]}: {resource[1]}")
                elif isinstance(resource, dict) and 'name' in resource and 'description' in resource:
                    print(f"- {resource['name']}: {resource['description']}")
                else:
                    print(f"- {resource}")

            # Ler a configuração da API Waha
            print("\n=== Lendo configuração do WhatsApp ===")
            try:
                config_content, mime_type = await session.read_resource("waha://configuracao")
                print(f"Configuração: {config_content}")
            except Exception as e:
                print(f"Erro ao ler recurso: {e}")

            # Verificar status do WhatsApp
            print("\n=== Verificando status do WhatsApp ===")
            try:
                status = await session.call_tool("verificar_conexao_whatsapp")
                print(f"Status do WhatsApp: {status}")
            except Exception as e:
                print(f"Erro ao verificar status: {e}")

            # Demonstração da integração GROQ
            print("\n=== Demonstração da integração com GROQ ===")
            print("Simularemos a análise de uma mensagem usando o GROQ...")
            
            # Criar uma mensagem fictícia para demonstrar o callback do GROQ
            demo_message = types.CreateMessageRequestParams(
                model="groq:llama3-8b-8192", 
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text="Por favor, envie uma mensagem de WhatsApp explicando o que é o modelo GROQ"
                        )
                    )
                ]
            )
            
            # Chamar o callback de amostragem manualmente para demonstração
            groq_response = await handle_sampling_message(demo_message)
            print(f"\nResposta do GROQ: {groq_response.content.text}")
            
            # Enviar uma mensagem de WhatsApp usando o GROQ
            print("\n=== Enviar mensagem de WhatsApp usando análise do GROQ ===")
            numero = input("Digite o número de telefone (ex: 5511999999999): ")
            mensagem = "Esta é uma mensagem enviada via integração GROQ-MCP-WhatsApp! 🤖"
            
            print(f"\nPredição do GROQ sobre o número: {await call_groq_api(f'Análise do número de telefone {numero}')}")
            
            print("\nEnviando mensagem via WhatsApp...")
            try:
                result = await session.call_tool(
                    "enviar_mensagem_whatsapp",
                    arguments={"numero": numero, "mensagem": mensagem}
                )
                print(f"Resultado: {result}")
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

if __name__ == "__main__":
    asyncio.run(run()) 