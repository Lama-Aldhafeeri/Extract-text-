import arabic_reshaper
from bidi.algorithm import get_display
import os
import os.path
import pdfplumber as pdfplumber
from flask import Flask, render_template, request, session
from werkzeug.utils import secure_filename
from flask_babel import Babel, gettext
from pdfminer.layout import LTTextLineHorizontal, LTTextBoxHorizontal
from ArabicOcr import arabicocr
from numba import jit, cuda
from pdf2image import convert_from_path

app = Flask(__name__, template_folder='templates', static_folder='staticFiles')
app.config['UPLOAD_FOLDER'] = 'files/'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
babel = Babel(app)

@babel.localeselector
def get_locale():
    # if session.get('lang') == 'ar':
    #    return 'ar'
    # else:
    #    return 'en'
    return request.accept_languages.best_match(['en', 'ar'])
    # return 'ar'

# @jit(target_backend='cuda')
def extract_text_from_img(path):
    out_image = 'out.jpg'
    results = arabicocr.arabic_ocr(path, out_image)
    print(results)
    words = []
    text = ""
    for i in range(len(results)):
        word = results[i][1]
        words.append(word)
    for w in range(len(words)):
        wordi = words[w]
        text += wordi + " "
    return text

def extract_text_from_pdf_method1(pdf_path):
    text = ''
    poppler_path = r'C:\Program Files\poppler-0.68.0\bin'
    images = convert_from_path(pdf_path=pdf_path, poppler_path=poppler_path)
    # save all pages in images folder
    images_path = "files\\images"
    for count, img in enumerate(images):
        img_name = f"{images_path}\\page_{count}.png"
        img.save(img_name, "PNG")
    for root, dirs, imgs in os.walk(images_path):
        for i in imgs:
            setPages(f"{images_path}\\{i}")
            text += extract_text_from_img(f"{images_path}\\{i}")
    return text
def setPages(pages):
    pass

def extract_text_from_pdf_method2(pdf_path, language_chosen):
    content = ""
    with pdfplumber.open(pdf_path) as pdf:
        totalpages = len(pdf.pages)
        for i in range(0, totalpages):
            pageobj = pdf.pages[i].layout
            for element in pageobj:
                if isinstance(element, LTTextBoxHorizontal):
                    for line in element:
                        if language_chosen == "Arabic":
                            content += line.get_text()[::-1]
                        else:
                            content += line.get_text()
        return content
import webbrowser

# Open URL in a new tab, if a browser window is already open.

@app.route('/', methods=['POST', 'GET'])
def upload_file():

    if request.method == "POST":
        print(request.files)
        pdf_file = request.files['file']  # Access the file
        #language_chosen = request.form['Language_chosen']  # Access the value of radio button
        # lang = request.form['lang']
        # language = get_user_lang(lang)

        if pdf_file.filename == '':
            print("File name is invalid")
            return render_template("DesignThePage.html", variable=gettext("No file chosen"))
       # elif language_chosen is None:
          #  print("No language coden")
           # return render_template("DesignThePage.html", variable=gettext("Please choose the language of your pdf file"))

        # Upload The file
        filename = secure_filename(pdf_file.filename)
        pdf_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        path = f'files\\{filename}'
        text = ''
        if filename[-3: len(filename)] == 'pdf':
            text = extract_text_from_pdf_method1(path)
        else:
            text = extract_text_from_img(path)

        if text == '':
            return render_template("DesignThePage.html", variable=gettext("Sorry We Couldn't Find Text In Your File.."))
        return render_template("display_text_page.html", variable=text)
    # delete the file
    mypath = "files"
    for root, dirs, files in os.walk(mypath):
        for file in files:
            os.remove(os.path.join(root, file))

    return render_template("DesignThePage.html")

app.run()
