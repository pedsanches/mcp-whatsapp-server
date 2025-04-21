# MCP WhatsApp Server

Servidor baseado no [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) para integração com WhatsApp através da API Waha.

## Sobre o Projeto

Este servidor permite que assistentes IA compatíveis com MCP (como Claude) interajam diretamente com contatos no WhatsApp. O projeto utiliza a [Waha API](https://github.com/wppconnect-team/wa-js) como backend para comunicação com o WhatsApp Web.

## Funcionalidades

- ✅ Verificação do status de conexão do WhatsApp
- ✅ Envio de mensagens via número de telefone
- ✅ Envio de mensagens via nome de contato cadastrado
- ✅ Gerenciamento de contatos por nome
- ✅ Visualização de configurações do servidor

## Requisitos

- Python 3.7+
- API Waha em execução
- Biblioteca MCP (Fast MCP)

## Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/mcp-whatsapp-server.git
   cd mcp-whatsapp-server
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente em um arquivo `.env`:
   ```
   WAHA_API_URL=http://localhost:3000
   WAHA_SESSION_ID=default
   CONTATOS_FILE=caminho/para/contatos.json (opcional)
   ```

4. Configure seus contatos no arquivo `contatos.json`:
   ```json
   {
       "contatos": {
           "Nome1": "5511999999999",
           "Nome2": "5522888888888"
       }
   }
   ```

## Uso

1. Inicie a API Waha seguindo as [instruções oficiais](https://github.com/wppconnect-team/wa-js)

2. Execute o servidor MCP:
   ```bash
   python server.py
   ```

3. Use o servidor com um cliente MCP compatível (como Claude Desktop)

## Recursos MCP Disponíveis

### Resources

- `waha://configuracao` - Configurações da API Waha
- `waha://status` - Status atual da conexão WhatsApp
- `waha://contatos` - Lista de contatos mapeados por nome

### Ferramentas (Tools)

- `verificar_conexao_whatsapp()` - Verifica o status atual da conexão
- `enviar_mensagem_whatsapp(numero, mensagem)` - Envia mensagem por número

## Exemplos

### Verificar Status da Conexão
```python
status = verificar_conexao_whatsapp()
print(f"Status: {status['mensagem']}")
```

### Enviar Mensagem por Número
```python
resultado = enviar_mensagem_whatsapp("5511999999999", "Olá! Esta é uma mensagem de teste.")
print(f"Resultado: {resultado['mensagem']}")
```

### Enviar Mensagem por Nome
```python
resultado = enviar_mensagem_por_nome("Pedro", "Olá! Esta é uma mensagem de teste.")
print(f"Resultado: {resultado['mensagem']}")
```

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob [MIT License](LICENSE).

## Imagens e Demonstração

As imagens de demonstração do projeto estão armazenadas na pasta `docs/images/`. Você pode adicionar suas próprias capturas de tela seguindo estas etapas:

1. Adicione suas imagens na pasta `docs/images/`
2. Referencie-as no README usando a sintaxe markdown:

```markdown
![Descrição da imagem](docs/images/nome-da-imagem.png)
```

### Exemplos de uso

![Claude enviando mensagem](docs/images/example1.png)

![Mensagem enviada](docs/images/example2.png)

*Nota: Substitua estas referências por suas próprias imagens depois de adicioná-las.*