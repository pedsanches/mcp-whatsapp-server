#!/usr/bin/env python3
"""
Cliente MCP para servidor WhatsApp utilizando a API real do GROQ
"""

import os
import asyncio
import json
import requests
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

async def call_groq_api(prompt_text, model="llama3-70b-8192"):
    """
    Chama a API do GROQ para gerar texto usando a API real
    """
    print(f"\n[GROQ API] Chamando modelo {model} com prompt:")
    print(f"---\n{prompt_text}\n---")
    
    # Configurar o cabeçalho de autenticação
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Configurar o corpo da requisição
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    # Fazer a chamada à API do GROQ
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        response.raise_for_status()  # Levantar exceção para erros HTTP
        
        # Processar a resposta
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "API do GROQ não retornou uma resposta válida."
    
    except requests.RequestException as e:
        print(f"Erro ao chamar a API do GROQ: {e}")
        return f"Erro na chamada à API do GROQ: {str(e)}"

# Callback para processar mensagens de amostragem (sampling)
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    """
    Processa mensagens usando o GROQ como modelo de linguagem
    """
    # Extrair o texto do prompt
    messages = []
    for msg in message.messages:
        if hasattr(msg, 'content') and hasattr(msg.content, 'text'):
            if isinstance(msg.content, types.TextContent):
                messages.append({
                    "role": msg.role,
                    "content": msg.content.text
                })
    
    # Formatar prompt para o GROQ
    prompt = """Você é um assistente especializado em WhatsApp que ajuda a criar mensagens e analisar números de telefone.
Seja conciso, útil e direto nas suas respostas.

"""
    
    if messages:
        # Adicionar as mensagens ao prompt
        for msg in messages:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
    
    # Chamar a API do GROQ
    response_text = await call_groq_api(prompt)
    
    # Retornar o resultado formatado
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text=response_text,
        ),
        model="groq:llama3-70b-8192",  # Especificar o modelo GROQ
        stopReason="endTurn",
    )

async def run():
    """
    Função principal que executa o cliente MCP com GROQ
    """
    print("Iniciando cliente MCP WhatsApp com integração GROQ real...")
    
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

            # Verificar status do WhatsApp
            print("\n=== Verificando status do WhatsApp com GROQ ===")
            try:
                # Consultar o GROQ sobre como verificar status
                status_prompt = "Como verificar o status do WhatsApp? Liste os passos técnicos."
                groq_advice = await call_groq_api(status_prompt)
                print(f"Dica do GROQ: {groq_advice}\n")
                
                # Verificar status real
                status = await session.call_tool("verificar_conexao_whatsapp")
                print(f"Status do WhatsApp: {status}")
                
                # Analisar o status com GROQ
                status_analysis = await call_groq_api(f"Analise o seguinte status do WhatsApp e explique de forma simples se está conectado: {status}")
                print(f"\nAnálise do GROQ: {status_analysis}")
            except Exception as e:
                print(f"Erro ao verificar status: {e}")

            # Enviar uma mensagem de WhatsApp usando o GROQ para gerar conteúdo
            print("\n=== Enviar mensagem gerada pelo GROQ ===")
            numero = input("Digite o número de telefone (ex: 5511999999999): ")
            
            # Pedir ao GROQ para analisar o número
            numero_analysis = await call_groq_api(f"Analise o seguinte número de telefone: {numero}. É um formato válido para WhatsApp? De qual região/operadora pode ser?")
            print(f"\nAnálise do número pelo GROQ: {numero_analysis}")
            
            # Pedir ao GROQ para gerar uma mensagem
            topic = input("Sobre qual assunto você quer enviar uma mensagem? ")
            message_prompt = f"Crie uma mensagem curta (máximo 200 caracteres) para WhatsApp sobre o seguinte assunto: {topic}. A mensagem deve ser amigável e incluir um emoji."
            
            mensagem = await call_groq_api(message_prompt)
            print(f"\nMensagem gerada pelo GROQ: {mensagem}")
            
            if input("\nEnviar esta mensagem? (s/n): ").lower() == 's':
                print("\nEnviando mensagem via WhatsApp...")
                try:
                    result = await session.call_tool(
                        "enviar_mensagem_whatsapp",
                        arguments={"numero": numero, "mensagem": mensagem}
                    )
                    print(f"Resultado: {result}")
                    
                    # Analisar o resultado com GROQ
                    result_analysis = await call_groq_api(f"Analise o resultado do envio da mensagem WhatsApp e explique em português simples se foi bem-sucedido: {result}")
                    print(f"\nAnálise do resultado pelo GROQ: {result_analysis}")
                except Exception as e:
                    print(f"Erro ao enviar mensagem: {e}")

if __name__ == "__main__":
    asyncio.run(run()) 