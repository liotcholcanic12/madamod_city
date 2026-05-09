from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def index():
    return "hello world"

@app.route('/api/test')
def test():
    return jsonify({"status": "ok"})
