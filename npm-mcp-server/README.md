# Servidor MCP para WhatsApp (Waha)

Este projeto implementa um servidor MCP (Model Context Protocol) para o Cursor que permite enviar mensagens via WhatsApp usando a API Waha.

## Pré-requisitos

1. Node.js instalado no seu computador
2. Uma instalação funcionando da API Waha (WhatsApp HTTP API)
3. Cursor com suporte a MCP

## Instalação

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências:

```bash
npm install
```

3. Configure a URL da sua API Waha no arquivo `.cursor/mcp.json`

## Configuração no Cursor

### Opção 1: Usando transporte stdio (padrão)

1. Certifique-se de que o diretório `.cursor` existe na raiz do seu projeto
2. Configure o arquivo `.cursor/mcp.json` para usar o transporte stdio:

```json
{
  "mcpServers": {
    "waha-server": {
      "command": "node",
      "args": ["waha-mcp-server.js"],
      "env": {
        "WAHA_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

3. Abra o Cursor e ele deve detectar automaticamente o servidor MCP

### Opção 2: Usando transporte SSE (recomendado se stdio não funcionar)

1. Inicie o servidor SSE separadamente em um terminal:

```bash
npm run start:sse
```

2. Configure o arquivo `.cursor/mcp.json` para usar o transporte SSE:

```json
{
  "mcpServers": {
    "waha-server": {
      "transport": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

3. Abra o Cursor e ele deve se conectar ao servidor MCP em execução

## Como usar

Depois de configurado, você pode usar a ferramenta no Cursor dizendo algo como:

"Use a ferramenta enviar_mensagem_whatsapp para enviar uma mensagem para o número 5511999999999 com o texto 'Olá, teste de mensagem via MCP'."

## Notas importantes

- O recurso (resource) "configuracao_waha" está implementado, mas atualmente o Cursor não suporta recursos MCP, apenas ferramentas.
- Certifique-se de que a API Waha está funcionando corretamente antes de usar esta ferramenta.
- Os números de telefone devem ser informados no formato internacional, sem '+' ou espaços (ex: 5511999999999).
- Se estiver tendo problemas com o modo stdio, tente usar o modo SSE que é mais confiável em alguns ambientes.

## Instalando a API Waha

Se você ainda não tem a API Waha instalada, siga estas etapas:

1. Clone o repositório do Waha:
```bash
git clone https://github.com/waha-api/waha.git
```

2. Entre no diretório e instale as dependências:
```bash
cd waha
npm install
```

3. Inicie o servidor:
```bash
npm start
```

4. Escaneie o código QR que aparecerá para conectar sua conta do WhatsApp 