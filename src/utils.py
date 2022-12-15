import hashlib
from flask import session

from src.database import Database


SALT = "abcd" # Should be secret env var!

def make_secret(password):
    return hashlib.md5((password + SALT).encode()).hexdigest()

def init_session(username):
    session['username'] = username
    session['recent_recipe_ids'] = ''
    
def add_recipe_id_to_session(recipe_id):
    if str(recipe_id) not in get_recent_recipe_ids():
        session['recent_recipe_ids'] += f'{recipe_id}|'

def get_recent_recipe_ids():
    recent = session['recent_recipe_ids'].split('|')
    return [id for id in recent if id]

def check_user_owns_recipe(username, recipe_id):
    data = Database.query(f"""
                   SELECT *
                   FROM Recipe
                   WHERE postedBy='{username}' AND recipeID='{recipe_id}'
                   """)
    
    return len(data) > 0