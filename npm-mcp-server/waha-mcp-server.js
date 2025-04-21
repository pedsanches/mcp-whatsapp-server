const axios = require('axios');

// URL da API Waha (vem da variável de ambiente)
const WAHA_API_URL = process.env.WAHA_API_URL || 'http://localhost:3000';

// Função para enviar mensagem via Waha
async function enviarMensagemWaha(numero, mensagem) {
  try {
    const response = await axios.post(`${WAHA_API_URL}/api/sendText`, {
      chatId: `${numero}@c.us`,
      text: mensagem
    });
    return { 
      sucesso: true, 
      resposta: response.data,
      mensagem: `Mensagem enviada com sucesso para ${numero}`
    };
  } catch (error) {
    return { 
      sucesso: false, 
      erro: error.message,
      mensagem: `Falha ao enviar mensagem para ${numero}: ${error.message}`
    };
  }
}

// Definição da tool para o MCP
const tools = [
  {
    name: "enviar_mensagem_whatsapp",
    description: "Envia uma mensagem de texto via WhatsApp usando a API Waha",
    parameters: {
      type: "object",
      properties: {
        numero: {
          type: "string",
          description: "Número de telefone completo com código do país (sem '+' ou espaços, ex: 5511999999999)"
        },
        mensagem: {
          type: "string",
          description: "Conteúdo da mensagem a ser enviada"
        }
      },
      required: ["numero", "mensagem"]
    },
    handler: async ({ numero, mensagem }) => {
      return await enviarMensagemWaha(numero, mensagem);
    }
  }
];

// Definição do resource (note que recursos ainda não são suportados no Cursor conforme documentação)
const resources = [
  {
    name: "configuracao_waha",
    description: "Configurações para a API Waha",
    schema: {
      type: "object",
      properties: {
        apiUrl: {
          type: "string",
          description: "URL da API Waha"
        },
        sessionId: {
          type: "string", 
          description: "ID da sessão Waha (opcional)"
        }
      }
    },
    data: {
      apiUrl: WAHA_API_URL,
      sessionId: "default"
    }
  }
];

// Protocolo MCP para comunicação stdio
process.stdin.setEncoding('utf8');
let inputBuffer = '';

process.stdin.on('data', (chunk) => {
  inputBuffer += chunk;
  processBuffer();
});

function processBuffer() {
  const messages = inputBuffer.split('\n');
  
  // Último item pode estar incompleto
  inputBuffer = messages.pop() || '';
  
  messages.forEach(message => {
    if (message.trim()) {
      try {
        const request = JSON.parse(message);
        handleRequest(request);
      } catch (error) {
        console.error(`Erro ao processar mensagem: ${error.message}`);
      }
    }
  });
}

async function handleRequest(request) {
  const { id, method, params } = request;
  
  let result;
  
  if (method === 'mcp.list_tools') {
    result = { tools };
  } else if (method === 'mcp.list_resources') {
    result = { resources };
  } else if (method === 'mcp.invoke_tool') {
    const { tool_name, parameters } = params;
    const tool = tools.find(t => t.name === tool_name);
    
    if (tool) {
      try {
        result = await tool.handler(parameters);
      } catch (error) {
        result = { error: error.message };
      }
    } else {
      result = { error: `Ferramenta não encontrada: ${tool_name}` };
    }
  } else {
    result = { error: `Método desconhecido: ${method}` };
  }
  
  const response = {
    jsonrpc: '2.0',
    id,
    result
  };
  
  process.stdout.write(JSON.stringify(response) + '\n');
}

// Iniciar o servidor
console.error('Servidor MCP Waha iniciado. Aguardando comandos...'); 