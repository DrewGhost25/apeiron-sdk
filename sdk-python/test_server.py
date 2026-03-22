from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/data/preview')
def preview():
    return jsonify({"test": "funziona"})

if __name__ == '__main__':
    app.run(port=5001)