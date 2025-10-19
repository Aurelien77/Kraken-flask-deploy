from flask import Flask, render_template, send_file, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
import threading
import time

app = Flask(__name__)

RANDOM_ARTICLE_URL = "https://fr.wikipedia.org/wiki/Sp%C3%A9cial:Page_au_hasard"

driver = None
current_title = ""
current_url = ""
last_image_data = b""
lock = threading.Lock()

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

# Initialisation du driver une seule fois
try:
    driver = create_driver()
except Exception as e:
    print("Erreur lors de la création du driver:", e)
    driver = None

def capture_article():
    global current_title, current_url
    if driver is None:
        raise RuntimeError("Le driver Selenium n'est pas initialisé!")

    driver.get(RANDOM_ARTICLE_URL)
    time.sleep(3)
    try:
        title_element = driver.find_element("id", "firstHeading")
        current_title = title_element.text
    except:
        current_title = "Article Wikipédia"
    current_url = driver.current_url

    screenshot_png = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(screenshot_png))

    width, height = image.size
    start_y = int(height * 0.35)
    cropped_image = image.crop((0, start_y, width, height))
    cropped_image.thumbnail((1200, 1000))

    bio = io.BytesIO()
    cropped_image.save(bio, format="PNG")
    bio.seek(0)
    return bio

@app.route("/")
def index():
    return render_template("index.html", title=current_title)

@app.route("/screenshot")
def screenshot():
    global last_image_data
    with lock:
        bio = io.BytesIO()
        bio.write(last_image_data)
        bio.seek(0)
    return send_file(bio, mimetype='image/png')

@app.route("/new_article")
def new_article():
    global last_image_data
    with lock:
        bio = capture_article()
        last_image_data = bio.getvalue()
        return jsonify({
            "title": current_title,
            "url": current_url,
            "img_timestamp": int(time.time() * 1000)
        })

@app.route("/article_link")
def article_link():
    return jsonify({"url": current_url, "title": current_title})

# --- Capture initiale ---
with lock:
    if driver is not None:
        bio = capture_article()
        last_image_data = bio.getvalue()

if __name__ == "__main__":
    app.run(debug=True)
