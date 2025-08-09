from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/price", methods=["POST"])
def calculate_price():
    data = request.get_json()
    base_price = data.get("base_price", 0)
    demand_factor = data.get("demand_factor", 1)
    competitor_price = data.get("competitor_price", base_price)

    optimized_price = (base_price + competitor_price) / 2 * demand_factor
    return jsonify({"optimized_price": round(optimized_price, 2)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
