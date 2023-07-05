from flask import Flask, request, jsonify
from scipy.optimize import linprog
from flask_cors import CORS
import os
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS

@app.route('/allocate', methods=['POST'])
def allocate_budget():
    try:
        data = request.get_json()
        channels = data['channels']
        budget = data['budget']
        min_budgets = data['min_budgets']
        max_budgets = data['max_budgets']
        min_sales = data['min_sales']
        max_sales = data['max_sales']
        
        num_channels = len(channels)

        # Objective function coefficients (negative for maximization)
        c = [-channel['roi'] for channel in channels]

        # Equality constraint (budget)
        A_eq = [[1] * num_channels]
        b_eq = [budget]

        # Inequality constraints
        A_ub = []
        b_ub = []

        # Min/max budget constraints
        for i in range(num_channels):
            A_ub.append([1 if j == i else 0 for j in range(num_channels)])
            b_ub.append(max_budgets[i])
            A_ub.append([-1 if j == i else 0 for j in range(num_channels)])
            b_ub.append(-min_budgets[i])

        # Min/max sales constraints
        for i in range(num_channels):
            A_ub.append([channels[i]['roi'] if j == i else 0 for j in range(num_channels)])
            b_ub.append(max_sales[i])
            A_ub.append([-channels[i]['roi'] if j == i else 0 for j in range(num_channels)])
            b_ub.append(-min_sales[i])

        # Solve the problem
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method='highs')
        allocation = result.x.tolist() if result.success else None
        
        # Calculate the expected revenue
        expected_revenue = sum(allocation[i] * channels[i]['roi'] for i in range(num_channels)) if allocation else None
        
        return jsonify({
            "allocation": allocation,
            "expected_revenue": expected_revenue
        })
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.debug = True  # Enable debug mode
    port = int(os.environ.get('PORT', 5000))  # Use PORT if it's there
    app.run(host='0.0.0.0', port=port)
