# Servidor MCP Python para WhatsApp

Este é um servidor MCP (Model Context Protocol) desenvolvido em Python para integração com a API Waha (WhatsApp).

## Requisitos

- Python 3.9 ou superior
- [MCP SDK para Python](https://github.com/modelcontextprotocol/python-sdk)
- API Waha em execução

## Instalação

1. Clone o repositório
2. Instale as dependências:
```
pip install -r requirements.txt
```

## Utilização

### Servidor

#### Como servidor stdio (para Claude Desktop)

```
python server.py
```

#### Como servidor web (SSE)

```
python server_sse.py
```

### Clientes

#### Cliente para servidor stdio

```
python client_stdio.py
```

#### Cliente para servidor SSE

```
python client_sse.py
```

### Variáveis de ambiente

- `WAHA_API_URL`: URL da API Waha (padrão: http://localhost:3000)
- `WAHA_SESSION_ID`: ID da sessão do WhatsApp (padrão: default)
- `MCP_PORT`: Porta para o servidor SSE (padrão: 8000)
- `MCP_SERVER_URL`: URL completa do servidor SSE (para clientes, padrão: http://localhost:8000)

## Recursos

O servidor oferece:

- 🔧 **Tools**: 
  - `enviar_mensagem_whatsapp`: Envia mensagens pelo WhatsApp
  - `verificar_conexao_whatsapp`: Verifica se o WhatsApp está conectado
- 📄 **Resources**: 
  - `waha://configuracao`: Configurações da API Waha
  - `waha://status`: Status atual da conexão com o WhatsApp
  - `waha://contatos`: Lista de contatos mapeados por nome
- 💬 **Prompts**: Templates para criação de mensagens (apenas na versão SSE)

## Solução de Problemas

### Códigos de Status da API Waha

A API Waha pode retornar diferentes códigos de status ao enviar mensagens:

- **200 (OK)**: Mensagem processada com sucesso
- **201 (Created)**: Mensagem criada com sucesso (também considerado sucesso)
- **4xx/5xx**: Erros diversos que são tratados com mensagens específicas

### Erro 422 Unprocessable Entity

Se você receber este erro ao enviar mensagens, verifique:

1. **Formato do número**: Deve conter apenas dígitos (ex: 5511999999999)
2. **Conexão do WhatsApp**: Use a ferramenta `verificar_conexao_whatsapp` para verificar se o WhatsApp está conectado
3. **API Waha**: Certifique-se de que a API Waha está em execução e configurada corretamente
4. **Autenticação do WhatsApp**: Na interface da API Waha, verifique se o QR code foi escaneado

## Notas de implementação

### Formato de URI para Recursos

No MCP Python SDK, os recursos devem ser definidos com URIs válidas. Por exemplo:
```python
@mcp.resource("waha://configuracao")
def configuracao_waha():
    # ...
```

### Verificação de Status do WhatsApp

O servidor verifica automaticamente o status do WhatsApp ao iniciar e antes de cada envio de mensagem:

```python
status = verificar_status_waha()
if status.get("status") == "error":
    # Tratar erro de conexão
```

### Parâmetros de Envio de Mensagem

O servidor envia mensagens com os seguintes parâmetros:

```python
response = requests.post(
    f"{WAHA_API_URL}/api/sendText",
    json={
        "chatId": f"{numero}@c.us", 
        "reply_to": None, 
        "text": mensagem, 
        "linkPreview": True, 
        "linkPreviewHighQuality": False, 
        "session": SESSION_ID
    }
)
```

### Formatos de resposta do servidor

O MCP pode retornar dados em diferentes formatos, dependendo da implementação e versão. Os clientes devem estar preparados para lidar com:

1. **Objetos com atributos**:
```python
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

2. **Tuplas ou listas**:
```python
for tool in tools:
    print(f"- {tool[0]}: {tool[1]}")
```

3. **Dicionários**:
```python
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

Os clientes neste projeto estão preparados para lidar com todos esses formatos.

### Implementação de Clientes

Os clientes MCP podem se conectar ao servidor de duas formas:

1. **Stdio** - Para servidores que usam entrada/saída padrão:
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Trabalhar com a sessão aqui
```

2. **HTTP/SSE** - Para servidores web:
```python
from mcp import ClientSession
from mcp.client.http import http_client
import aiohttp

async with aiohttp.ClientSession() as http_session:
    async with http_client(http_session, "http://localhost:8000") as (read, write):
        async with ClientSession(read, write) as session:
            # Trabalhar com a sessão aqui
```

Para mais informações, consulte a [documentação do MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk). 