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

        num_channels = len(channels)

        # Objective function coefficients (negative for maximization)
        c = [-channel['roi'] for channel in channels]

        # Equality constraint (budget)
        A_eq = [[1] * num_channels]
        b_eq = [budget]

        # Inequality constraints
        A_ub = []
        b_ub = []

        # Budget or sales constraints
        for i in range(num_channels):
            if 'min_budget' in channels[i] or 'max_budget' in channels[i]:
                if 'min_budget' in channels[i]:
                    A_ub.append([-1 if j == i else 0 for j in range(num_channels)])
                    b_ub.append(-channels[i]['min_budget'])

                if 'max_budget' in channels[i]:
                    A_ub.append([1 if j == i else 0 for j in range(num_channels)])
                    b_ub.append(channels[i]['max_budget'])

            if 'min_sale' in channels[i] or 'max_sale' in channels[i]:
                if 'min_sale' in channels[i]:
                    A_ub.append([-channels[i]['roi'] if j == i else 0 for j in range(num_channels)])
                    b_ub.append(-channels[i]['min_sale'])

                if 'max_sale' in channels[i]:
                    A_ub.append([channels[i]['roi'] if j == i else 0 for j in range(num_channels)])
                    b_ub.append(channels[i]['max_sale'])

        # Solve the problem
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method='highs')

        if result.success:
            allocation = result.x.tolist()
        else:
            allocation = None

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
