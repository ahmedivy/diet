import numpy as np
import pandas as pd
from typing import List, Optional
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpMaximize


# Read the dataset in a global var
df = pd.read_csv("data/products-cleaned.csv")


def get_suggestions(cart, user_info):
    """
    Get suggestions for modifying the cart based on user information and nutritional recommendations.

    Args:
        cart (dict): Dictionary representing the products in the cart and their quantities.
        user_info (dict): Dictionary containing user information such as gender, weight, height, age, days, diet, and allergies.

    Returns:
        tuple: A tuple containing the description of the suggested action ("No suggestions", "Remove products", or "Add products")
               and the items to be modified in the cart. The items can be None if no modifications are suggested.
    """
    # Get the cart matrix
    cart_matrix = get_cart_matrix(cart)

    # Calculate nutritional recommendations
    recommendations = calculate_recommendations(
        gender=user_info.get('gender'),
        weight=user_info.get('weight'),
        height=user_info.get('height'),
        age=user_info.get('age'),
        days=user_info.get('days'),
        vector=True
    )

    # Get the products matrix
    products_matrix = get_products_matrix(
        user_info.get('diet'),
        user_info.get('allergies')
    )

    # Get suggestions based on the cart and nutritional recommendations
    description, items = lp_get_suggestions(cart_matrix, products_matrix, recommendations, cart)

    return description, items


def get_all_products(preference: str, allergies: list) -> List[dict]:
    """
    Returns a list of all products in the dataset.

    Returns:
        List[dict]: List of all products in the dataset.
    """
    products = df.copy()

    # Filter the products by category based on the preference
    if preference == 'vegetarian':
        products = products[products['Category'] != 'Non-Veggie']
    elif preference == 'non-vegetarian':
        products = products[products['Category'] != 'Veggie']


    # Filter the products by allergies
    for allergy in allergies:
        products = products[~products['Product'].str.contains(allergy, case=False)]

    products = products[["Code", "Product"]]
    products = products.rename(columns={"Product": "name", "Code": "code"})
    return products.to_dict(orient="records")


def calculate_recommendations(
    gender: str, weight: float, height: float, age: int, days: int, vector=False
) -> dict:
    """
    Calculate daily nutritional recommendations based on gender, weight, height, age, and number of days.

    Args:
        gender (str): The gender of the person ('male' or 'female').
        weight (float): The weight of the person in kilograms.
        height (float): The height of the person in centimeters.
        age (int): The age of the person in years.
        days (int): The number of days to calculate the recommendations for.
        vector (bool, optional): If True, return the recommendations as a numpy array. Defaults to False.

    Returns:
        dict or np.ndarray: The daily nutritional recommendations as a dictionary or numpy array,
                            depending on the value of the `vector` parameter.
    """

    # Calculate BMR
    if gender.lower() == "male":
        bmr = 66.5 + (13.75 * weight) + (5 * height) - (6.75 * age)
    elif gender.lower() == "female":
        bmr = 655 + (9.56 * weight) + (1.85 * height) - (4.68 * age)

    # Define the nutritional values
    calories = bmr * 1.2
    fats = weight * 0.4
    proteins = weight * 1.2
    carbohydrates = (calories - (fats * 9) - (proteins * 4)) / 4
    cholesterol = 300
    sugars = 30

    # Adjust the nutritional values for the number of days and return them
    if vector:
        nutrients = np.array([proteins, fats, carbohydrates, calories, cholesterol, sugars])
        nutrients *= days
        return nutrients

    nutrients = {
        "Proteins": proteins * days,
        "Fats": fats * days,
        "Carbohydrates": carbohydrates * days,
        "Calories": calories * days,
        "Cholesterol": cholesterol * days,
        "Sugars": sugars * days,
    }

    # Change nutrient to not exceed more than 2 decimals
    nutrients = {k: round(v, 2) for k, v in nutrients.items()}
    return nutrients


def get_cart_nutrients(cart: dict) -> dict:
    """
    Get the nutritional values of the products in the cart.

    Args:
        cart (dict): Dictionary representing the products in the cart and their quantities.

    Returns:
        dict: Dictionary containing the nutritional values of the products in the cart.
    """

    products = df[df['Code'].isin([int(code) for code in cart.keys()])]
    products = products[["Proteins", "Fats", "Carbohydrates", "Calories", "Cholesterol", "Sugars"]]
    products_arr = products.to_numpy()
    products_arr = products_arr * np.array(list(cart.values())).reshape(-1, 1)
    products_arr = np.sum(products_arr, axis=0)
    # Change nutrient to not exceed more than 2 decimals
    products_arr = {k: round(v, 2) for k, v in zip(products.columns, products_arr)}
    return products_arr


def lp_add_products(
    prod_matrix: np.ndarray, cart_matrix: np.ndarray, recommendations: np.ndarray, recursive_calls=0
) -> Optional[List[dict]]:
    """
    Generate a list of products to add to the user's cart based on nutritional recommendations.

    Args:
        prod_matrix (np.ndarray): Matrix of product IDs and their nutritional values.
        cart_matrix (np.ndarray): Matrix of products already in the user's cart.
        recommendations (np.ndarray): Nutritional recommendations.
        recursive_calls (int, optional): Number of recursive calls made. Defaults to 0.

    Returns:
        Optional[List[int]]: List of product IDs and quantities to add to the user's cart,
                             or None if a solution cannot be found.
    """

    # Sample products from the dataset
    n_samples = min(200*max(recursive_calls, 1), prod_matrix.shape[0])
    sample_indices = np.random.choice(prod_matrix.shape[0], n_samples, replace=False)
    sample = prod_matrix[sample_indices]
    sample = np.concatenate((sample, cart_matrix[:, :-1]), axis=0)
    sample = np.unique(sample, axis=0)

    # Separate the products and nutrients
    products = sample[:, 0]
    nutrients = sample[:, 1:]

    # Define the tolerance (10% error)
    tolerance = 0.1

    # Create the LP problem
    problem = LpProblem("AddProducts", LpMinimize)

    # Create decision variables for the quantities
    quantities = LpVariable.dicts("Quantity", products, lowBound=0, cat="Integer")

    # Define the objective function
    objective = lpSum(quantities[p] for p in products)
    problem += objective

    # Define the constraints for the nutritional values
    for i in range(nutrients.shape[1]):
        problem += lpSum(nutrients[ix, i] * quantities[p] for ix, p in enumerate(products)) >= (1 - tolerance) * recommendations[i]
        problem += lpSum(nutrients[ix, i] * quantities[p] for ix, p in enumerate(products)) <= (1 + tolerance) * recommendations[i]

    # Define constraints that products quantities cannot be negative and greater than 1
    for p in products:
        if p in cart_matrix[:, 0]:
            continue
        problem += quantities[p] >= 0
        problem += quantities[p] <= 1

    # Add constraints based on the user's cart that they must have the same quantities
    for item in cart_matrix:
        prod_code, prod_quantity = item[0], item[-1]
        problem += quantities[prod_code] == prod_quantity

    # Solve the problem
    problem.solve()

    # Return products if the problem is solved, otherwise call the function recursively
    if problem.status == 1:
        to_add = [
            {
                "code": int(p),
                "name": df[df['Code'] == int(p)]['Product'].values[0],
                "quantity": quantities[p].value(),
            }
            for p in products
            if quantities[p].value() != 0 and p not in cart_matrix[:, 0]
        ]
        return to_add
    elif recursive_calls < 5:
        return lp_add_products(prod_matrix, cart_matrix, recommendations, recursive_calls + 1)
    else:
        return None


def get_products_matrix(preference: str, allergies: list) -> np.ndarray:
    """
    Get the matrix of selected product columns based on preference and allergies.

    Args:
        preference (str): User's preference ('vegetarian' or 'non-vegetarian').
        allergies (list): List of allergies to filter out products.

    Returns:
        np.ndarray: Matrix of selected product columns.
    """

    # Define the columns to select
    cols = ['Code', 'Proteins', 'Fats', 'Carbohydrates', 'Calories', 'Cholesterol', 'Sugars']

    # Create a copy of the products dataframe
    products = df.copy()

    # Filter the products by category based on the preference
    if preference == 'vegetarian':
        products = products[products['Category'] != 'Non-Veggie']
    elif preference == 'non-vegetarian':
        products = products[products['Category'] != 'Veggie']

    # Filter the products by allergies
    for allergy in allergies:
        products = products[~products['Product'].str.contains(allergy)]

    # Return the matrix of selected columns
    return products[cols].to_numpy()


def lp_remove_products(cart_matrix, recommendation_vector, cart):
    """
    Optimize the removal of products from the cart to satisfy nutritional recommendations.

    Args:
        cart_matrix (np.ndarray): Matrix representing the products in the cart and their nutritional values.
        recommendation_vector (np.ndarray): Nutritional recommendations.
        cart (dict): Dictionary representing the products in the cart and their quantities.

    Returns:
        List[dict] or None: List of products to remove from the cart to satisfy recommendations,
                            or None if a solution cannot be found.
    """

    # Create a linear programming problem
    problem = LpProblem("Nutrition Optimization", LpMaximize)

    # Separate out the products, nutrients, and quantities
    products = cart_matrix[:, 0]
    nutrients = cart_matrix[:, 1:-1]
    cart_quantities = cart_matrix[:, -1]

    # Create decision variables
    quantities = LpVariable.dicts("Products", products, lowBound=0, cat="Integer")

    # Define the objective function
    problem += lpSum(quantities[p] for p in products)

    # Define the constraints
    for i in range(nutrients.shape[1]):
        problem += lpSum(nutrients[ix, i] * quantities[p] for ix, p in enumerate(products)) <= recommendation_vector[i]

    # Define constraints that quantities cannot be negative and greater than cart quantities
    for i, p in enumerate(products):
        problem += quantities[p] <= cart_quantities[i]

    # Solve the linear programming problem
    problem.solve()

    if problem.status != 1:
        return None

    to_remove = [
        {
            "code": int(p),
            "name": df[df['Code'] == int(p)]['Product'].values[0],
            "quantity": cart[str(int(p))] - quantities[p].value(),
        }
        for p in products
        if quantities[p].value() != cart[str(int(p))]
    ]

    return to_remove


def lp_get_suggestions(cart_matrix, products_matrix, recommendations, cart):
    """
    Get suggestions for optimizing the cart to satisfy nutritional recommendations.

    Args:
        cart_matrix (np.ndarray): Matrix representing the products in the cart and their nutritional values.
        products_matrix (np.ndarray): Matrix representing the nutritional values of available products.
        recommendations (np.ndarray): Nutritional recommendations.
        cart (dict): Dictionary representing the products in the cart and their quantities.

    Returns:
        str, List[dict] or None: Type of suggestion ('No suggestions', 'Remove products', 'Add products'),
                                 and the optimized list of products to remove or add.
    """

    # Calculate the total nutrients in the cart
    nutrients = cart_matrix[:, 1:-1]
    cart_quantities = cart_matrix[:, -1]
    nutrients = np.multiply(nutrients, cart_quantities.reshape(-1, 1))
    total_nutrients = np.sum(nutrients, axis=0)

    # Define the tolerance (10% error)
    tolerance = 0.1

    # Check if the current cart satisfies the nutritional requirements
    if np.all(abs(total_nutrients - recommendations) <= tolerance * recommendations):
        return "No suggestions", None

    # Check if the cart exceeds the nutritional requirements
    if np.any(total_nutrients > recommendations):
        optimized = lp_remove_products(cart_matrix, recommendations, cart)
        return "Remove products", optimized

    else:
        optimized = lp_add_products(products_matrix, cart_matrix, recommendations)
        if optimized is None:
            return "Remove products", lp_remove_products(cart_matrix, recommendations, cart)
        else:
            return "Add products", optimized


def get_cart_matrix(cart: dict) -> np.ndarray:
    """
    Convert the cart dictionary to a np matrix representation

    Args:
        cart (dict): Dictionary representing the products in the cart and their quantities.

    Returns:
        np.ndarray: Matrix representing the products in the cart and their nutritional values.
    """

    # Get the products from the dataset based on the cart keys
    codes = list(map(int, list(cart.keys())))
    products = df[df['Code'].isin(codes)]

    # Get the nutritional values from the dataset
    cols = ['Code', 'Proteins', 'Fats', 'Carbohydrates', 'Calories', 'Cholesterol', 'Sugars']
    matrix = np.array(products[cols])

    # Concatenate the quantities to the matrix as a last column
    quantities = np.array(list(cart.values())).reshape(-1, 1)
    matrix = np.concatenate((matrix, quantities), axis=1)

    return matrix
