from flask import Flask, request, render_template, redirect, url_for, session
import pymysql

from src.utils import make_secret, init_session, add_recipe_id_to_session, get_recent_recipe_ids, check_user_owns_recipe
from src.database import Database

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('recent_recipe_ids', None)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        secret_password = make_secret(password)
        query = f"""
                SELECT *
                FROM Person
                WHERE userName = '{username}' AND password = '{secret_password}'
                """
                
        data = Database.query(query)
        
        if len(data) > 0:
            init_session(username)
            return redirect(url_for('index'))
        
        return '''
            Login Failed! Please try again...<br>
            <<a href="/login">Login</a>
        '''
    
    return '''
        Please login<br>
        <form method="post">
            <p><label for="username">Username:</label>
            <p><input type=text name=username>
            <p><label for="password">Password:</label>
            <p><input type=text name=password>
            <p><input type=submit value=Login>
        </form>
        
         <a href="/register">Register</a>
    '''
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        profile = request.form['profile']
        stored_password = make_secret(password)
        query = f"""
                INSERT INTO Person (userName, password, fName, lName, email, profile)
                VALUES (
                    '{username}',
                    '{stored_password}',
                    '{fname}',
                    '{lname}',
                    '{email}',
                    '{profile}'
                )
                """
        
        Database.insert(query)
        
        init_session(username)
        return redirect(url_for('index'))

    return '''
        <form method="post">
            <p><label for="username">Username:</label>
            <p><input type=text name=username>
            <p><label for="password">Password:</label>
            <p><input type=text name=password>
            <p><label for="fname">First Name:</label>
            <p><input type=text name=fname>
            <p><label for="lname">Last Name:</label>
            <p><input type=text name=lname>
            <p><label for="email">Email:</label>
            <p><input type=text name=email>
            <p><label for="profile">Profile Info:</label>
            <p><input type=text name=profile>
            <p><input type=submit value=Login>
        </form>
    '''
@app.route('/')
@app.route('/index')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    return render_template("index.html")

@app.route('/recipes')
def recipes():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    return render_template("query_recipes.html")

@app.get('/recipes/search')
def get_recipes():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    num_stars = request.args['num_stars']
    tag = request.args['tag']
    if not any([num_stars, tag]):
        return render_template("invalid_page.html", error_msg="number of stars or tag must be provided"), 400
    
    if tag and num_stars:
        query = f"""
            SELECT DISTINCT(recipeID)
            FROM Recipe LEFT JOIN RecipeTag
            USING(recipeID)
            LEFT JOIN Review
            USING(recipeID)
            WHERE tagText = '{tag}'
            AND stars = '{num_stars}'
            """
    elif num_stars and not tag:
        query = f"""
            SELECT DISTINCT(recipeID)
            FROM Recipe LEFT JOIN RecipeTag
            USING(recipeID)
            LEFT JOIN Review
            USING(recipeID)
            WHERE stars = '{num_stars}'
            """
    elif tag and not num_stars:
        query = f"""
            SELECT DISTINCT(recipeID)
            FROM Recipe LEFT JOIN RecipeTag
            USING(recipeID)
            LEFT JOIN Review
            USING(recipeID)
            WHERE tagText = '{tag}'
            """
    else:
        return render_template("invalid_page.html", error_msg="number of stars or tag must be provided"), 400

    data = Database.query(query)
    for recipe in data:
        add_recipe_id_to_session(recipe['recipeID'])
            
    return render_template("show_recipes.html", recipes=data, tag=tag, num_stars=num_stars)
    
@app.get("/recipes/new")
def new_recipes_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    ingredients = Database.query("""
                                 SELECT iNAme
                                 FROM Ingredient
                                 """)
    ingredients = [ingredient['iNAme'] for ingredient in ingredients]
    
    units = Database.query("""
                                 SELECT unitName
                                 FROM Unit
                                 """)
    units = [unit['unitName'] for unit in units]
    
    
    return render_template("post_recipe.html", ingredients=ingredients, units=units)

@app.post("/recipes/ingredient/new")
def new_recipe_ingredient():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    recipe_id = request.form['recipeID']
    ingredient = request.form['iName']
    unit = request.form['unitName']
    amnt = request.form['amount']
    
    if not check_user_owns_recipe(session.get('username'), recipe_id):
        return "User not allowed to edit a recipe they do not own!"
    
        
    insert_ingredient_query = f"""
                            INSERT INTO RecipeIngredient (recipeID, iName, unitName, amount)
                            VALUES ('{recipe_id}', '{ingredient}', '{unit}', '{amnt}')
                            """
    
    Database.insert(insert_ingredient_query)
    return f"inserted ingredient for recipe {recipe_id}!"
    
    
    
@app.post("/recipes/new")
def post_new_recipe():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    title = request.form['title']
    num_servings = request.form['numServings']
    tags = request.form['tags']
    posted_by = request.form['username']
    
    insert_recipe_query = f"""
                        INSERT INTO Recipe (title, numServings, postedBy)
                        VALUES ('{title}', {num_servings}, '{posted_by}')
                        """

    Database.insert(insert_recipe_query)
    
    get_recipe_id_query = f"""
                        SELECT recipeID
                        FROM Recipe
                        WHERE title='{title}' AND numServings='{num_servings}' AND postedBy='{posted_by}'
                        ORDER BY recipeID DESC
                        """
                        
    data = Database.query_one(get_recipe_id_query)
    recipe_id = data['recipeID']
    add_recipe_id_to_session(recipe_id)
                        
    if len(tags) > 0 and not tags.isspace():
        for tag in tags.split(','):
            insert_tag_query = f"""
                                INSERT INTO RecipeTag (recipeID, tagText)
                                VALUES ('{recipe_id}', '{tag}')
                                """
            Database.insert(insert_tag_query)

    
    return f"posted recipe {recipe_id}"

@app.get('/recipes/new/step')
def new_recipe_step():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    query = f"""
            SELECT recipeID 
            FROM Recipe 
            ORDER BY recipeID ASC
            """

    data = Database.query(query)
    recipes = []
    for recipe in data:
        recipes.append(recipe['recipeID'])
        add_recipe_id_to_session(recipe['recipeID'])
    
    return render_template("post_recipe_step.html", recipe_ids=recipes)
    
@app.post('/recipes/new/step')
def post_new_recipe_step():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    recipe_id = request.form['recipe_id']
    add_recipe_id_to_session(recipe_id)
    step_no = request.form['step_number']
    s_desc = request.form['step_desc']
    
    query = f"""
            INSERT INTO Step (stepNo, recipeID, sDesc)
            VALUES ({step_no}, '{recipe_id}', '{s_desc}')
            """
    Database.insert(query)
    
    return f"Inserted Step {step_no} for recipe {recipe_id}"

@app.get('/recipes/review')
def new_review_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    return render_template("post_review.html")

@app.get('/recipes/search/reviews')
def get_recipe_reviews():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    recipe_id = request.args.get('recipe_id', "")
    if not recipe_id:
        return "Invalid Recipe ID"
    
    add_recipe_id_to_session(recipe_id)
        
    query = f"""
        SELECT *
        FROM Review
        WHERE recipeID='{recipe_id}'
        """
    data = Database.query(query)
    
    return render_template("show_reviews.html", reviews=data, recipe_id=recipe_id)

@app.post('/recipes/review')
def post_review():
    if not session.get('username'):
        return redirect(url_for('login'))
    

    username = request.form['username']
    recipe_id = request.form['recipe_id']
    num_stars = request.form['stars']
    review_desc = request.form['review_desc']
    review_title = request.form['review_title']
    
    query = f"""
        INSERT INTO Review (
            userName,
            recipeID,
            revTitle,
            revDesc,
            stars
        )
        VALUES (
            '{username}',
            '{recipe_id}',
            '{review_title}',
            '{review_desc}',
            '{num_stars}'
        )
            """
    Database.insert(query)
    add_recipe_id_to_session(recipe_id)
    
    return redirect(url_for('index'))


@app.get('/recipes/search_by_recipeid')
def get_recipe_info():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    recipe_id = request.args['recipe_id']
    recipe_steps_query =f"""
            SELECT *
            FROM Recipe LEFT JOIN STEP
            USING (recipeID)
            LEFT JOIN RecipePicture
            USING (recipeID)
            WHERE Recipe.recipeID={recipe_id}
        """
    recipe_steps_data = Database.query(recipe_steps_query)
    recipe_ingredients_query =f"""
            SELECT *
            FROM Recipe LEFT JOIN RecipeIngredient
            USING (recipeID)
            WHERE Recipe.recipeID={recipe_id}
        """
    recipe_ingredients_data = Database.query(recipe_ingredients_query)
    
    
    if len(recipe_steps_data) < 1:
        return "No data found for this recipe!"
    
    add_recipe_id_to_session(recipe_id)
    
    return render_template("show_recipe_info.html", recipe_steps=recipe_steps_data, recipe_ingredients=recipe_ingredients_data)

@app.get("/recipes/recent")
def get_recently_viewed_recipes():
    if not session.get('username'):
        return redirect(url_for('login'))
    

    if len(get_recent_recipe_ids()) < 1:
        return "No recipes recently viewed!"
    
    query = f"""
            SELECT *
            FROM Recipe
            WHERE recipeID IN {tuple(session['recent_recipe_ids'])}
            """
    data = Database.query(query)
    
    return render_template("show_recent_recipes.html", recipes=data)

