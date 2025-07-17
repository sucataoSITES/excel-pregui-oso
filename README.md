# Analisador de Fichas com IA

Sistema web completo para análise automática de fichas usando ChatGPT ou OCR tradicional, com geração de planilhas Excel organizadas.

## Funcionalidades

- 📤 Upload múltiplo de imagens de fichas
- 🤖 Análise inteligente usando ChatGPT (recomendado) ou OCR tradicional
- 📊 Extração automática de informações estruturadas
- 📋 Geração de planilhas Excel organizadas
- 🎨 Interface moderna e responsiva
- ⚡ Deploy fácil no Render

## Tecnologias Utilizadas

### Backend
- Flask (Python)
- OpenAI API (ChatGPT)
- Pytesseract (OCR)
- Pandas (manipulação de dados)
- OpenPyXL (geração de Excel)

### Frontend
- React
- Tailwind CSS
- Shadcn/UI
- Vite

## Estrutura do Projeto

```
image-analyzer-app/
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── image_analyzer.py  # Rotas principais
│   │   │   └── user.py
│   │   ├── models/
│   │   ├── static/               # Frontend construído
│   │   └── main.py              # Aplicação principal
│   ├── requirements.txt
│   └── render.yaml              # Configuração do Render
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── App.jsx              # Componente principal
│   └── package.json
└── README.md
```

## Instalação Local

### Pré-requisitos
- Python 3.11+
- Node.js 20+
- Tesseract OCR (para funcionalidade OCR)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

### Variáveis de Ambiente
Crie um arquivo `.env` no diretório backend com:
```
OPENAI_API_KEY=sua_chave_openai_aqui
OPENAI_API_BASE=https://api.openai.com/v1
```

## Execução Local

### Desenvolvimento
1. Backend:
```bash
cd backend
source venv/bin/activate
python src/main.py
```

2. Frontend (em outro terminal):
```bash
cd frontend
npm run dev
```

### Produção Local
1. Construir frontend:
```bash
cd frontend
npm run build
```

2. Copiar arquivos para Flask:
```bash
cp -r frontend/dist/* backend/src/static/
```

3. Executar apenas o backend:
```bash
cd backend
source venv/bin/activate
python src/main.py
```

## Deploy no Render

### Método 1: Via GitHub (Recomendado)

1. **Criar repositório no GitHub:**
   - Faça upload de todo o conteúdo da pasta `backend/` para um repositório
   - Inclua o arquivo `render.yaml` na raiz

2. **Configurar no Render:**
   - Acesse [render.com](https://render.com)
   - Conecte sua conta GitHub
   - Clique em "New Web Service"
   - Selecione seu repositório
   - O Render detectará automaticamente o `render.yaml`

3. **Configurar variáveis de ambiente:**
   - No painel do Render, vá em "Environment"
   - Adicione:
     - `OPENAI_API_KEY`: sua chave da OpenAI
     - `OPENAI_API_BASE`: `https://api.openai.com/v1`

### Método 2: Deploy Manual

1. **Preparar arquivos:**
   - Construa o frontend: `cd frontend && npm run build`
   - Copie para o Flask: `cp -r frontend/dist/* backend/src/static/`

2. **Fazer upload no Render:**
   - Crie um novo Web Service
   - Faça upload da pasta `backend/`
   - Configure as variáveis de ambiente

## Configuração da API OpenAI

1. **Obter chave da API:**
   - Acesse [platform.openai.com](https://platform.openai.com)
   - Crie uma conta ou faça login
   - Vá em "API Keys" e crie uma nova chave

2. **Configurar no Render:**
   - Adicione a chave como variável de ambiente `OPENAI_API_KEY`

## Como Usar

1. **Acesse a aplicação** no navegador
2. **Selecione o método de análise:**
   - ChatGPT (recomendado): mais preciso e inteligente
   - OCR Tradicional: funciona offline, menos preciso
3. **Faça upload das imagens** das fichas
4. **Clique em "Analisar Imagens"**
5. **Aguarde o processamento**
6. **Visualize os resultados** extraídos
7. **Baixe a planilha Excel** com os dados organizados

## Campos Extraídos

O sistema extrai automaticamente os seguintes campos das fichas:
- Cliente
- Data
- Telefone
- Marca
- Modelo
- Motor
- Placa
- Ano
- Serviço
- Quantidade
- Valor Unitário (R$)
- Valor Total (R$)
- Desconto (R$)
- Total Final (R$)
- Garantia

## Limitações

- **ChatGPT**: Requer chave da API OpenAI (paga)
- **OCR**: Funciona melhor com imagens de alta qualidade e texto legível
- **Tamanho**: Máximo 50MB por upload
- **Formatos**: PNG, JPG, JPEG, GIF, BMP, TIFF

## Solução de Problemas

### Erro de API OpenAI
- Verifique se a chave está correta
- Confirme se há créditos na conta OpenAI
- Teste com o método OCR como alternativa

### Erro de OCR
- Instale o Tesseract OCR no servidor
- Verifique a qualidade das imagens
- Use imagens com texto bem legível

### Erro de Deploy
- Confirme que todas as dependências estão no `requirements.txt`
- Verifique se as variáveis de ambiente estão configuradas
- Consulte os logs do Render para detalhes

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Consulte a documentação das APIs utilizadas
- Verifique os logs de erro para diagnóstico

