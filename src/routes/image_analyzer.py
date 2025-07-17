import os
import base64
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pandas as pd
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import openai
import json
from datetime import datetime

image_analyzer_bp = Blueprint("image_analyzer", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")

# Criar diretórios se não existirem
for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_data_from_chatgpt_response(content):
    """Tenta extrair um objeto JSON de uma string de resposta do ChatGPT."""
    try:
        # Tentar encontrar o JSON na string
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON da resposta do ChatGPT.")
    return None

def get_empty_data_structure():
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
        "Garantia": "",
    }

def analyze_with_chatgpt(image_path):
    """Analisa imagem usando ChatGPT Vision"""
    try:
        client = openai.OpenAI()

        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        prompt_text = (
            "Você é um assistente especializado em extrair informações de fichas de serviço automotivo. "
            "A imagem fornecida é uma foto de um documento físico, que pode conter escrita manual, "
            "rasuras, ou estar em condições de iluminação variadas. "
            "Sua tarefa é analisar cuidadosamente a imagem e extrair as seguintes informações em formato JSON. "
            "Seja o mais preciso possível, mesmo que a escrita seja um pouco ilegível ou a foto não seja perfeita. "
            "Se um campo não estiver visível, não puder ser determinado com certeza, ou estiver vazio, deixe-o vazio. "
            "Para valores monetários, extraia apenas os números, sem símbolos de moeda (R$, $). "
            "A saída DEVE ser um objeto JSON válido e completo, com todos os campos listados abaixo, mesmo que vazios. "
            "Não adicione nenhum texto explicativo antes ou depois do JSON, apenas o JSON puro.\n\n" +
            json.dumps(get_empty_data_structure(), indent=4) + "\n"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )

        content = response.choices[0].message.content
        extracted_data = extract_data_from_chatgpt_response(content)

        if extracted_data:
            return {"data": extracted_data, "raw_output": content}
        else:
            print(f"ChatGPT não retornou JSON válido. Conteúdo: {content[:200]}...")
            return {"data": get_empty_data_structure(), "raw_output": content}

    except openai.APIError as e:
        print(f"Erro da API OpenAI: {e}")
        return {"data": get_empty_data_structure(), "raw_output": f"Erro da API OpenAI: {e}"}
    except Exception as e:
        print(f"Erro inesperado na análise com ChatGPT: {e}")
        return {"data": get_empty_data_structure(), "raw_output": f"Erro inesperado: {e}"}

def analyze_with_ocr(image_path):
    """Analisa imagem usando OCR (pytesseract) com pré-processamento avançado para maior precisão."""
    try:
        img = Image.open(image_path)

        # 1. Converter para escala de cinza
        img = img.convert("L")

        # 2. Aumentar contraste e nitidez
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0) # Aumenta o contraste em 2x
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0) # Aumenta a nitidez em 2x

        # 3. Binarização adaptativa (melhor para fundos irregulares)
        # Usando um limiar mais agressivo para escrita manual
        img = img.point(lambda x: 0 if x < 180 else 255, "1") # Limiar ajustado para 180

        # 4. Remover ruído (opcional, pode borrar texto fino)
        # img = img.filter(ImageFilter.MedianFilter(size=3))

        texto = pytesseract.image_to_string(img, lang="por")
        linhas = texto.split("\n")

        dados = get_empty_data_structure()

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

        for linha in linhas:
            if "eixo" in linha.lower() or "bomba" in linha.lower():
                dados["Serviço"] += linha.strip() + "; "

        return {"data": dados, "raw_output": texto}

    except Exception as e:
        print(f"Erro na análise com OCR: {e}")
        return {"data": get_empty_data_structure(), "raw_output": f"Erro inesperado: {e}"}

@image_analyzer_bp.route("/upload", methods=["POST"])
def upload_images():
    """Endpoint para upload e análise de imagens"""
    try:
        if "images" not in request.files:
            return jsonify({"error": "Nenhuma imagem enviada no campo \"images\"."}), 400

        files = request.files.getlist("images")
        analysis_method = request.form.get("method", "chatgpt")

        if not files or all(file.filename == "" for file in files):
            return jsonify({"error": "Nenhuma imagem selecionada para upload."}), 400

        registros = []
        processed_files = []
        errors = []
        raw_outputs = [] # Nova lista para armazenar saídas brutas

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                try:
                    file.save(filepath)
                except Exception as e:
                    errors.append(f"Erro ao salvar o arquivo {filename}: {str(e)}")
                    continue

                result = None
                if analysis_method == "chatgpt":
                    result = analyze_with_chatgpt(filepath)
                    if not result["data"] or all(value == '' for key, value in result["data"].items() if key != 'Arquivo'): # Fallback se ChatGPT falhar ou retornar vazio
                        print(f"ChatGPT falhou ou retornou dados vazios para {filename}. Tentando OCR...")
                        result = analyze_with_ocr(filepath)
                else:
                    result = analyze_with_ocr(filepath)

                dados = result["data"]
                raw_outputs.append({"filename": unique_filename, "output": result["raw_output"]}) # Armazena a saída bruta

                if dados and any(value != '' for key, value in dados.items() if key != 'Arquivo'): # Verifica se há dados extraídos
                    dados["Arquivo"] = unique_filename
                    registros.append(dados)
                    processed_files.append(unique_filename)
                else:
                    errors.append(f"Não foi possível extrair dados significativos de {filename} com nenhum método.")

            else:
                errors.append(f"Arquivo inválido ou não permitido: {file.filename}")

        if not registros:
            error_message = "Não foi possível processar nenhuma imagem ou extrair dados significativos." 
            if errors: 
                error_message += " Erros específicos: " + "; ".join(errors)
            return jsonify({"error": error_message, "raw_outputs": raw_outputs}), 400

        return jsonify({
            "message": f"{len(registros)} imagens processadas com sucesso.",
            "data": registros,
            "files": processed_files,
            "method_used": analysis_method,
            "errors": errors,
            "raw_outputs": raw_outputs
        })

    except Exception as e:
        return jsonify({"error": f"Erro interno no servidor: {str(e)}"}), 500

@image_analyzer_bp.route("/generate-excel", methods=["POST"])
def generate_excel():
    """Gera arquivo Excel com os dados analisados"""
    try:
        data = request.json
        if not data or "records" not in data:
            return jsonify({"error": "Dados não fornecidos para geração do Excel."}), 400

        registros = data["records"]

        df = pd.DataFrame(registros)

        if "Arquivo" in df.columns:
            df = df.drop("Arquivo", axis=1)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fichas_resultado_{timestamp}.xlsx"
        filepath = os.path.join(RESULTS_FOLDER, filename)

        df.to_excel(filepath, index=False)

        return send_file(filepath, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({"error": f"Erro na geração do Excel: {str(e)}"}), 500

@image_analyzer_bp.route("/health", methods=["GET"])
def health_check():
    """Endpoint para verificar se o serviço está funcionando"""
    return jsonify({"status": "ok", "message": "Serviço de análise de imagens funcionando"})


