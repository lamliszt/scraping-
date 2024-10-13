from flask import Flask, render_template, request, send_file
import pandas as pd
from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content, parse_with_ollama
from langchain_ollama import OllamaLLM

app = Flask(__name__)

# Khởi tạo mô hình Ollama
model = OllamaLLM(model="llama3.1")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_urls', methods=['POST'])
def process_urls():
    urls = request.form.getlist('urls')  # Lấy danh sách các URL từ biểu mẫu
    results = []

    # Bước 1: Quét nội dung từ các URL
    all_content = []
    for url in urls:
        try:
            html_content = scrape_website(url)
            body_content = extract_body_content(html_content)
            cleaned_content = clean_body_content(body_content)
            all_content.append(cleaned_content)
        except Exception as e:
            return render_template('index.html', error=f"Lỗi quét trang {url}: {str(e)}")

    # Bước 2: Phân tích nội dung với Ollama
    for url, content in zip(urls, all_content):
        result = {}  # Kết quả cho từng URL
        try:
            dom_chunks = split_dom_content(content, max_length=6000)
            parse_description = "Tóm tắt bài viết này, nêu rõ các điểm chính và các ý quan trọng. Đừng quên cung cấp các thông tin chi tiết nếu có."
            parsed_result = parse_with_ollama(dom_chunks, parse_description)

            # Tính số lượng từ
            word_count = len(content.split())

            result['URL website'] = url
            result['Số lượng từ đếm được'] = word_count
            result['Nội dung chính'] = parsed_result
            result['Lỗi'] = None

        except Exception as e:
            result['URL website'] = url
            result['Số lượng từ đếm được'] = 0
            result['Nội dung chính'] = ""
            result['Lỗi'] = str(e)

        results.append(result)  # Thêm kết quả vào danh sách

    # Tạo DataFrame từ kết quả và lưu thành file Excel
    df = pd.DataFrame(results)
    output_file = 'results.xlsx'
    df.to_excel(output_file, index=False)

    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

