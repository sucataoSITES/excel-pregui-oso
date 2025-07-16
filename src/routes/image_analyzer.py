import os
import base64
import pytesseract
from PIL import Image
import pandas as pd
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import openai
from datetime import datetime

image_analyzer_bp = Blueprint('image_analyzer', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')

# Criar diretórios se não existirem
for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_with_chatgpt(image_path):
    """Analisa imagem usando ChatGPT Vision"""
    try:
        client = openai.OpenAI()
        
        # Converter imagem para base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analise esta imagem de ficha/documento e extraia as seguintes informações em formato JSON:
                            {
                                "Cliente": "",
                                "Data": "",
                                "Telefone": "",
                                "Marca": "",
                                "Modelo": "",
                                "Motor": "",
                                "Placa": "",
                                "Ano": "",
                                "Serviço": "",
                                "Quantidade": "",
                                "Valor Unitário (R$)": "",
                                "Valor Total (R$)": "",
                                "Desconto (R$)": "",
                                "Total Final (R$)": "",
                                "Garantia": ""
                            }
                            
                            Extraia apenas as informações visíveis na imagem. Se algum campo não estiver presente, deixe vazio. Para valores monetários, extraia apenas os números (sem R$ ou símbolos)."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Extrair JSON da resposta
        content = response.choices[0].message.content
        import json
        
        # Tentar extrair JSON da resposta
        try:
            # Procurar por JSON na resposta
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass
            
        # Se não conseguir extrair JSON, retornar estrutura vazia
        return {
            "Cliente": "",
            "Data": "",
            "Telefone": "",
            "Marca": "",
            "Modelo": "",
            "Motor": "",
            "Placa": "",
            "Ano": "",
            "Serviço": "",
            "Quantidade": "",
            "Valor Unitário (R$)": "",
            "Valor Total (R$)": "",
            "Desconto (R$)": "",
            "Total Final (R$)": "",
            "Garantia": ""
        }
        
    except Exception as e:
        print(f"Erro na análise com ChatGPT: {e}")
        return None

def analyze_with_ocr(image_path):
    """Analisa imagem usando OCR (pytesseract)"""
    try:
        texto = pytesseract.image_to_string(Image.open(image_path), lang='por')
        linhas = texto.split('\n')
        
        dados = {
            "Cliente": "",
            "Data": "",
            "Telefone": "",
            "Marca": "",
            "Modelo": "",
            "Motor": "",
            "Placa": "",
            "Ano": "",
            "Serviço": "",
            "Quantidade": "",
            "Valor Unitário (R$)": "",
            "Valor Total (R$)": "",
            "Desconto (R$)": "",
            "Total Final (R$)": "",
            "Garantia": ""
        }
        
        for linha in linhas:
            linha_lower = linha.lower()
            if "cliente" in linha_lower:
                dados["Cliente"] = linha.split(":")[-1].strip()
            elif "data" in linha_lower:
                dados["Data"] = linha.split(":")[-1].strip()
            elif "celular" in linha_lower or "tel" in linha_lower:
                dados["Telefone"] = linha.split(":")[-1].strip()
            elif "marca" in linha_lower:
                dados["Marca"] = linha.split(":")[-1].strip()
            elif "modelo" in linha_lower:
                dados["Modelo"] = linha.split(":")[-1].strip()
            elif "motor" in linha_lower:
                dados["Motor"] = linha.split(":")[-1].strip()
            elif "placa" in linha_lower:
                dados["Placa"] = linha.split(":")[-1].strip()
            elif "ano" in linha_lower:
                dados["Ano"] = linha.split(":")[-1].strip()
            elif "garantia" in linha_lower:
                dados["Garantia"] = linha.strip()
            elif "valor total" in linha_lower:
                dados["Valor Total (R$)"] = linha.split("R$")[-1].strip()
            elif "valor unit" in linha_lower:
                dados["Valor Unitário (R$)"] = linha.split("R$")[-1].strip()
            elif "quant" in linha_lower:
                dados["Quantidade"] = linha.split(":")[-1].strip()
            elif "desconto" in linha_lower:
                dados["Desconto (R$)"] = linha.split("R$")[-1].strip()
        
        # Extrair serviços
        for linha in linhas:
            if "eixo" in linha.lower() or "bomba" in linha.lower():
                dados["Serviço"] += linha.strip() + "; "
                
        return dados
        
    except Exception as e:
        print(f"Erro na análise com OCR: {e}")
        return None

@image_analyzer_bp.route('/upload', methods=['POST'])
def upload_images():
    """Endpoint para upload e análise de imagens"""
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'Nenhuma imagem enviada'}), 400
        
        files = request.files.getlist('images')
        analysis_method = request.form.get('method', 'chatgpt')  # 'chatgpt' ou 'ocr'
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'Nenhuma imagem selecionada'}), 400
        
        registros = []
        processed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Analisar imagem
                if analysis_method == 'chatgpt':
                    dados = analyze_with_chatgpt(filepath)
                    if dados is None:  # Fallback para OCR se ChatGPT falhar
                        dados = analyze_with_ocr(filepath)
                else:
                    dados = analyze_with_ocr(filepath)
                
                if dados:
                    dados['Arquivo'] = filename
                    registros.append(dados)
                    processed_files.append(filename)
        
        if not registros:
            return jsonify({'error': 'Não foi possível processar nenhuma imagem'}), 400
        
        return jsonify({
            'message': f'{len(registros)} imagens processadas com sucesso',
            'data': registros,
            'files': processed_files,
            'method_used': analysis_method
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

@image_analyzer_bp.route('/generate-excel', methods=['POST'])
def generate_excel():
    """Gera arquivo Excel com os dados analisados"""
    try:
        data = request.json
        if not data or 'records' not in data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        registros = data['records']
        
        # Criar DataFrame
        df = pd.DataFrame(registros)
        
        # Remover coluna 'Arquivo' se existir (não queremos no Excel final)
        if 'Arquivo' in df.columns:
            df = df.drop('Arquivo', axis=1)
        
        # Gerar nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fichas_resultado_{timestamp}.xlsx"
        filepath = os.path.join(RESULTS_FOLDER, filename)
        
        # Salvar Excel
        df.to_excel(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': f'Erro na geração do Excel: {str(e)}'}), 500

@image_analyzer_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se o serviço está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Serviço de análise de imagens funcionando'})

