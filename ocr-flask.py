from flask import Flask, request, jsonify
from paddlex import create_pipeline   # 若你的paddleOCR或paddlex配置不同，请自行替换
from flask_cors import CORS
import pandas as pd
import tempfile
import traceback


app = Flask(__name__)
CORS(app)  # 允许跨域

# 假设使用 paddlex ocr pipeline
ocr_pipeline = create_pipeline('ocr')

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image part"}), 400
        image_file = request.files['image']
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            image_file.save(tmp.name)
            tmp_path = tmp.name

        output = list(ocr_pipeline(tmp_path))  # paddlex 结果
        # 提取rec_texts
        if output and isinstance(output, list):
            rec_texts = []
            # 兼容多个block
            for item in output:
                if isinstance(item, dict) and 'rec_texts' in item:
                    rec_texts.extend(item['rec_texts'])
            result_text = '\n'.join(rec_texts)
        else:
            result_text = str(output)

        return jsonify({"result": result_text})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    
def search_csv_value(query):
    chunksize = 10000
    found_rows = []
    csv_file = 'data.csv'
    for chunk in pd.read_csv(csv_file, chunksize=chunksize):
        matches = chunk[(chunk.astype(str) == str(query)).any(axis=1)]
        if not matches.empty:
            found_rows.append(matches)
    if found_rows:
        result_df = pd.concat(found_rows)
        result_df = result_df.iloc[::-1]
        return result_df.to_dict(orient='records')
    else:
        return []

@app.route('/search_excel', methods=['POST'])
def search_excel():
    try:
        data = request.get_json(force=True)
        query = data.get('query')
        if query is None:
            return jsonify({"result": "查询参数为空"}), 400
        result = search_csv_value(query)
        if not result:
            return jsonify({"result": "未查找到该内容"})
        return jsonify({"result": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"result": "CSV查询异常", "exception": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
