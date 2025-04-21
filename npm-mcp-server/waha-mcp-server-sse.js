const axios = require('axios');
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { v4: uuidv4 } = require('uuid');

// Configurações
const WAHA_API_URL = process.env.WAHA_API_URL || 'http://localhost:3000';
const MCP_PORT = process.env.MCP_PORT || 8000;

// Armazenar as conexões SSE ativas
const activeConnections = new Map();

// Função para enviar mensagem via Waha
async function enviarMensagemWaha(numero, mensagem) {
  try {
    const response = await axios.post(`${WAHA_API_URL}/api/sendText`, {
      chatId: `${numero}@c.us`,
      text: mensagem
    });
    return {
      status: "success",
      data: response.data,
      message: `Mensagem enviada com sucesso para ${numero}`
    };
  } catch (error) {
    console.error('Erro ao enviar mensagem Waha:', error);
    return {
      status: "error",
      error: error.message,
      message: `Falha ao enviar mensagem para ${numero}: ${error.message}`
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

// Criar aplicação Express
const app = express();

// Aumentar o tempo limite para evitar timeouts
app.use((req, res, next) => {
  res.setTimeout(120000); // 2 minutos
  next();
});

// Configurar CORS para permitir solicitações de qualquer origem
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Accept', 'Connection', 'Cache-Control']
}));

// Configurar o body parser para JSON com limites maiores
app.use(bodyParser.json({
  limit: '10mb'
}));

// Função para enviar evento SSE para cliente específico
function sendSSEEvent(res, data) {
  if (!res.writableEnded && !res.destroyed) {
    try {
      const payload = typeof data === 'string' ? data : JSON.stringify(data);
      res.write(`data: ${payload}\n\n`);
    } catch (err) {
      console.error(`[${new Date().toISOString()}] Erro ao enviar evento SSE:`, err);
    }
  }
}

// Função para enviar uma mensagem de log como notificação
function sendLogNotification(res, message, level = "info") {
  if (!res.writableEnded && !res.destroyed) {
    try {
      const notification = {
        jsonrpc: "2.0",
        method: "notifications/message",
        params: { 
          level: level, 
          data: message 
        }
      };
      sendSSEEvent(res, notification);
    } catch (err) {
      console.error(`[${new Date().toISOString()}] Erro ao enviar notificação:`, err);
    }
  }
}

// Endpoint SSE para conexão do cliente
app.get('/sse', (req, res) => {
  const sessionId = uuidv4();
  
  console.log(`[${new Date().toISOString()}] Nova conexão SSE estabelecida: ${sessionId}`);
  
  // Desativar timeouts para evitar que a conexão seja encerrada
  req.socket.setTimeout(0);
  req.socket.setNoDelay(true);
  req.socket.setKeepAlive(true);
  res.setTimeout(0);
  
  // Configurar cabeçalhos SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no', // Para Nginx
    'Access-Control-Allow-Origin': '*'
  });
  
  // Linha inicial exigida pelo SSE
  res.write('\n');
  
  // Armazenar a conexão
  activeConnections.set(sessionId, res);
  
  // Enviar evento endpoint para informar o cliente sobre o endpoint para enviar mensagens
  const endpointEvent = {
    jsonrpc: "2.0",
    method: "sse/endpoint",
    params: {
      endpoint: "/sse"  // O endpoint para enviar mensagens
    }
  };
  sendSSEEvent(res, endpointEvent);
  
  // Enviar mensagem de conexão estabelecida
  sendLogNotification(res, "Conexão SSE estabelecida");
  
  // Configurar keep-alive a cada 10 segundos
  const keepAliveInterval = setInterval(() => {
    if (!res.writableEnded && !res.destroyed) {
      res.write(': ping\n\n');
    } else {
      clearInterval(keepAliveInterval);
    }
  }, 10000);
  
  // Limpar recursos quando a conexão for fechada
  req.on('close', () => {
    console.log(`[${new Date().toISOString()}] Conexão SSE encerrada: ${sessionId}`);
    clearInterval(keepAliveInterval);
    activeConnections.delete(sessionId);
  });
  
  // Tratar erros na conexão
  req.on('error', (err) => {
    console.error(`[${new Date().toISOString()}] Erro na conexão SSE ${sessionId}:`, err);
    clearInterval(keepAliveInterval);
    activeConnections.delete(sessionId);
    if (!res.writableEnded) {
      res.end();
    }
  });
  
  // Tratar erros na resposta
  res.on('error', (err) => {
    console.error(`[${new Date().toISOString()}] Erro na resposta SSE ${sessionId}:`, err);
    clearInterval(keepAliveInterval);
    activeConnections.delete(sessionId);
  });
});

// Endpoint para processar mensagens JSON-RPC
app.post('/sse', async (req, res) => {
  const request = req.body;
  
  console.log(`[${new Date().toISOString()}] Requisição MCP recebida:`, JSON.stringify(request, null, 2));
  
  if (!request || !request.id) {
    return res.status(400).json({
      jsonrpc: "2.0",
      id: null,
      error: {
        code: -32600,
        message: "Requisição JSON-RPC inválida"
      }
    });
  }
  
  const { id, method, params } = request;
  
  try {
    // Verificar o método solicitado
    if (method === 'mcp.list_tools') {
      console.log(`[${new Date().toISOString()}] Listando ferramentas disponíveis`);
      
      // Notificar conexões ativas
      for (const [, connection] of activeConnections) {
        sendLogNotification(connection, "Listando ferramentas disponíveis");
      }
      
      // Responder com a lista de ferramentas
      return res.json({
        jsonrpc: "2.0",
        id,
        result: {
          tools
        }
      });
    } 
    else if (method === 'mcp.list_resources') {
      console.log(`[${new Date().toISOString()}] Listando recursos disponíveis`);
      
      // Responder com a lista de recursos
      return res.json({
        jsonrpc: "2.0",
        id,
        result: {
          resources
        }
      });
    } 
    else if (method === 'mcp.invoke_tool') {
      const { tool_name, parameters } = params;
      console.log(`[${new Date().toISOString()}] Invocando ferramenta: ${tool_name}`, JSON.stringify(parameters, null, 2));
      
      // Verificar se a ferramenta existe
      const tool = tools.find(t => t.name === tool_name);
      
      if (!tool) {
        return res.json({
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Ferramenta não encontrada: ${tool_name}`
          }
        });
      }
      
      // Verificar parâmetros e executar a ferramenta
      if (tool_name === 'enviar_mensagem_whatsapp') {
        const { numero, mensagem } = parameters;
        
        if (!numero || !mensagem) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32602,
              message: "Parâmetros inválidos: 'numero' e 'mensagem' são obrigatórios"
            }
          });
        }
        
        // Notificar ação
        for (const [, connection] of activeConnections) {
          sendLogNotification(connection, `Enviando mensagem para ${numero}`);
        }
        
        // Executar a ação
        const result = await enviarMensagemWaha(numero, mensagem);
        
        // Notificar resultado
        for (const [, connection] of activeConnections) {
          sendLogNotification(
            connection, 
            result.status === "success" 
              ? `Mensagem enviada com sucesso para ${numero}` 
              : `Erro ao enviar mensagem para ${numero}: ${result.error}`,
            result.status === "success" ? "info" : "error"
          );
        }
        
        // Responder com o resultado
        return res.json({
          jsonrpc: "2.0",
          id,
          result
        });
      } else {
        return res.json({
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Implementação da ferramenta não encontrada: ${tool_name}`
          }
        });
      }
    } 
    else {
      // Método desconhecido
      return res.json({
        jsonrpc: "2.0",
        id,
        error: {
          code: -32601,
          message: `Método desconhecido: ${method}`
        }
      });
    }
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Erro ao processar requisição MCP:`, error);
    
    // Responder com erro
    return res.json({
      jsonrpc: "2.0",
      id,
      error: {
        code: -32603,
        message: `Erro interno: ${error.message}`
      }
    });
  }
});

// Rota para debug de SSE (útil para diagnóstico)
app.get('/debug-sse', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Depurador SSE</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
          #log { background: #f5f5f5; border: 1px solid #ddd; padding: 10px; height: 300px; overflow-y: auto; }
          .event { margin-bottom: 5px; }
          .time { color: #666; font-size: 0.8em; }
        </style>
      </head>
      <body>
        <h1>Depurador de conexão SSE</h1>
        <div id="log"></div>
        <script>
          const log = document.getElementById('log');
          const source = new EventSource('/sse');
          
          function addLogEntry(message) {
            const entry = document.createElement('div');
            entry.className = 'event';
            const time = document.createElement('span');
            time.className = 'time';
            time.textContent = new Date().toISOString() + ': ';
            entry.appendChild(time);
            entry.appendChild(document.createTextNode(message));
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
          }
          
          source.onopen = function() {
            addLogEntry('Conexão SSE aberta');
          };
          
          source.onmessage = function(event) {
            addLogEntry('Mensagem recebida: ' + event.data);
          };
          
          source.onerror = function(event) {
            addLogEntry('Erro na conexão SSE');
            console.error(event);
          };
          
          window.addEventListener('beforeunload', function() {
            source.close();
          });
        </script>
      </body>
    </html>
  `);
});

// Rota para testar a API Waha
app.post('/test-waha', async (req, res) => {
  const { numero, mensagem } = req.body;
  
  if (!numero || !mensagem) {
    return res.status(400).json({
      status: 'error',
      message: 'Número e mensagem são obrigatórios'
    });
  }
  
  try {
    const result = await enviarMensagemWaha(numero, mensagem);
    return res.json(result);
  } catch (error) {
    return res.status(500).json({
      status: 'error',
      message: `Erro ao enviar mensagem: ${error.message}`
    });
  }
});

// Rota principal para mostrar informações do servidor
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Servidor MCP (SSE) para Waha</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          h1 { color: #2c3e50; }
          .status { background: #e8f5e9; padding: 10px; border-radius: 5px; margin: 20px 0; }
          .test-form { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
          .debug-links { margin: 20px 0; }
          .debug-links a { background: #f1f1f1; padding: 8px 15px; text-decoration: none; color: #333; border-radius: 4px; margin-right: 10px; }
          ul { background: #f8f9fa; padding: 15px 30px; border-radius: 5px; }
          li { margin: 10px 0; }
          code { background: #f1f1f1; padding: 2px 4px; border-radius: 3px; }
          button { background: #4CAF50; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
          input, textarea { width: 100%; padding: 8px; margin: 5px 0 15px; border: 1px solid #ddd; border-radius: 4px; }
        </style>
      </head>
      <body>
        <h1>Servidor MCP (SSE) para Waha</h1>
        <div class="status">
          <h3>Status: ✅ Servidor em execução</h3>
          <p>Este servidor implementa o protocolo MCP (Model Context Protocol) para integração com a API Waha.</p>
          <p>Conexões ativas: ${activeConnections.size}</p>
        </div>
        
        <div class="debug-links">
          <a href="/debug-sse" target="_blank">Verificar conexão SSE</a>
        </div>
        
        <h2>Endpoints disponíveis:</h2>
        <ul>
          <li><strong><a href="/sse">/sse</a></strong> - Endpoint SSE para conexão do Cursor</li>
          <li><strong>/sse</strong> - Endpoint para requisições JSON-RPC (POST)</li>
          <li><strong>/test-waha</strong> - Endpoint para testar envio de mensagens via Waha (POST)</li>
          <li><strong>/debug-sse</strong> - Página para depurar conexão SSE</li>
        </ul>
        
        <h2>Ferramentas disponíveis:</h2>
        <ul>
          ${tools.map(tool => `<li><strong>${tool.name}</strong>: ${tool.description}</li>`).join('')}
        </ul>
        
        <div class="test-form">
          <h2>Teste de envio de mensagem</h2>
          <form id="testForm">
            <div>
              <label for="numero">Número (com código do país, sem '+' ou espaços):</label>
              <input type="text" id="numero" name="numero" placeholder="5511999999999" required>
            </div>
            <div>
              <label for="mensagem">Mensagem:</label>
              <textarea id="mensagem" name="mensagem" rows="4" placeholder="Digite sua mensagem aqui" required></textarea>
            </div>
            <button type="submit">Enviar mensagem</button>
          </form>
          <div id="resultado"></div>
          
          <script>
            document.getElementById('testForm').addEventListener('submit', async (e) => {
              e.preventDefault();
              const numero = document.getElementById('numero').value;
              const mensagem = document.getElementById('mensagem').value;
              const resultadoDiv = document.getElementById('resultado');
              
              resultadoDiv.innerHTML = '<p>Enviando mensagem...</p>';
              
              try {
                const response = await fetch('/test-waha', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({ numero, mensagem })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                  resultadoDiv.innerHTML = '<p style="color: green;">Mensagem enviada com sucesso!</p>';
                } else {
                  resultadoDiv.innerHTML = '<p style="color: red;">Erro ao enviar mensagem: ' + data.message + '</p>';
                }
              } catch (error) {
                resultadoDiv.innerHTML = '<p style="color: red;">Erro na requisição: ' + error.message + '</p>';
              }
            });
          </script>
        </div>
      </body>
    </html>
  `);
});

// Iniciar servidor
app.listen(MCP_PORT, '0.0.0.0', () => {
  console.log(`[${new Date().toISOString()}] Servidor MCP (SSE) iniciado em 0.0.0.0:${MCP_PORT}`);
  console.log(`[${new Date().toISOString()}] Endpoint SSE: http://localhost:${MCP_PORT}/sse`);
  console.log(`[${new Date().toISOString()}] Ferramentas disponíveis:`);
  tools.forEach(tool => {
    console.log(`- ${tool.name}: ${tool.description}`);
  });
}); 