
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, render_template_string, g, redirect, Response, url_for, session
import query
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import shortuuid

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = "26533228" 

# apply the blueprints to the app
import auth
from auth import customer_login_required
app.register_blueprint(auth.bp)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
DATABASEURI = "postgresql://hz2653:787876@34.73.36.248/project1" # Modify this with your own credentials you received from Joseph!


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    cursor = query.all_city(g.conn)
    city = []
    for result in cursor:
        city.append(result)
    cursor.close()
    
    #find all cuisine types
    cursor = query.all_cuisine(g.conn)
    cuisine = []
    for result in cursor:
        cuisine.append(result)
    cursor.close()
    
    #find liked food
    if g.user_id:
        uid = session['user_id']
        fav_food_id = []
        cursor = query.fav_food(g.conn,uid)
        for result in cursor:
            fav_food_id.append(result.cuisine_id)
        cursor.close()
        #find recommended restaurants
        rec= []
        for f in fav_food_id:
            cursor = query.recommendation(g.conn,f)
            for result in cursor:
                rec.append(result)
            cursor.close()
        context = dict(city=city, cuisine=cuisine,rec=rec)
        return render_template('index.html', **context)
    else:
        context = dict(city=city, cuisine=cuisine)
        return render_template('index.html', **context)
"""
request is a special object that Flask provides to access web request information:

request.method:   "GET" or "POST"
request.form:     if the browser submitted a form, this contains the data in the form
request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
"""

  # DEBUG: this is debugging code to see what request looks like
  #print(request.args)


  #
  # example of a database query
  #
'''
cursor = g.conn.execute("SELECT name FROM test")
names = []
for result in cursor:
  names.append(result['name'])  # can also be accessed using result[0]
cursor.close()
'''

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  #context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  #return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
    
@app.route('/search-res', methods =['POST'])
def search_res():
    rname = request.form["name"]
    city = request.form.getlist("city")
    cuisine = request.form.getlist("check_type")
    cost = request.form.getlist("check_cost")
    if city==['']:
        cursor = query.all_city(g.conn)
        for result in cursor:
            city.append(result.city_name)
        cursor.close()    
    
    if len(cuisine)==0:
        cursor = query.all_cuisine(g.conn)
        for result in cursor:
            cuisine.append(result.cuisine_name)
        cursor.close()
        
    if len(cost)==0:
        cost=['$','$$','$$$','$$$$']
    
    cursor = query.search_res(g.conn,rname,city,cuisine,cost)
    res = []
    for result in cursor:
        res.append(result)
    cursor.close()
    
    context = dict(res=res)
    return render_template("restaurants.html", **context)


@app.route('/myprofile', methods = ['GET'])
def my_profile():
    conn = g.conn
    uid = session['user_id']
    my_info = conn.execute("SELECT * FROM customer WHERE customer_id = %s;", uid).fetchone()
    my_name = my_info['name']
    my_phone = my_info['phone_num']
    my_pwd = my_info['password']
    
    #find liked food types
    cursor = query.fav_food(conn, uid)
    fav_food = []
    for result in cursor:
        fav_food.append(result)
    cursor.close()
    
    cuisine = []
    cursor = query.all_cuisine(g.conn)
    for result in cursor:
        cuisine.append(result)
    cursor.close()
    
    #find friends
    cursor = conn.execute("SELECT customer_id_2 FROM is_friend WHERE customer_id_1 = %s", uid)
    friend_id=[]
    for result in cursor:
        friend_id.append(result.customer_id_2)
    cursor.close()
    cursor = conn.execute("SELECT customer_id_1 FROM is_friend WHERE customer_id_2 = %s", uid)
    for result in cursor:
        friend_id.append(result.customer_id_1)
    cursor.close()
    
    friend=[]
    for i in friend_id: 
        info = conn.execute("SELECT * FROM customer WHERE customer_id = %s", i).fetchone()
        friend.append(info)
    
    
    #friend request
    request = []    
    cursor = conn.execute("SELECT customer_id_1 FROM friend_request WHERE customer_id_2 = %s "\
                          "AND request_status = 'pending'" , uid)
    for result in cursor:
        request.append(result.customer_id_1)
    cursor.close()
    request_info =[]
    for r in request:
        info = conn.execute("SELECT * FROM customer WHERE customer_id = %s", r).fetchone()
        request_info.append(info)
    print(request_info)

    context = dict(my_name = my_name, my_phone = my_phone, cuisine = cuisine,
                   my_pwd = my_pwd, fav_food = fav_food, friend = friend, request_info=request_info)
    return render_template("myprofile.html", **context)

@app.route('/myprofile', methods = ['POST'])
def my_profile_edit():
    conn = g.conn
    uid = session['user_id']
    name = request.form["username"]
    phone = request.form["phone_number"]
    pwd = generate_password_hash(request.form["password"])
    fav_food = request.form.getlist("fav_food")
    friend_phone = request.form["friend_phone"]
        
    if request.form.get("update_name"):
        conn.execute("UPDATE customer SET name = %s WHERE customer_id = %s;", name, uid)
        return redirect(url_for("my_profile"))
            
    elif request.form.get("update_phone"):
        conn.execute("UPDATE customer SET phone_num = %s WHERE customer_id = %s;", phone, uid)
        return redirect(url_for("my_profile"))
        
    elif request.form.get("update_pwd"):
        conn.execute("UPDATE customer SET phone_num = %s WHERE customer_id = %s;", pwd, uid)
        return redirect(url_for("my_profile"))
        
    elif request.form.get("update_food"):
        conn.execute("DELETE FROM likes_cuisine WHERE customer_id = %s;", uid)
        for f in fav_food:
            conn.execute("INSERT INTO likes_cuisine VALUES (%s, %s);", uid, f)
        return redirect(url_for("my_profile"))
            
    elif request.form.get("accept_request"):
        req_id = request.form["accept_request"]
        conn.execute("UPDATE friend_request SET request_status = 'accepted' WHERE customer_id_1 = %s AND "\
                     "customer_id_2 = %s;", req_id, uid)
        conn.execute("INSERT INTO is_friend VALUES (%s, %s);", uid, req_id)
        return redirect(url_for("my_profile"))
        
    elif request.form.get("reject_request"):
        req_id = request.form["reject_request"]
        conn.execute("UPDATE friend_request SET request_status = 'rejected' WHERE customer_id_1 = %s AND "\
                     "customer_id_2 = %s;", req_id, uid)
        return redirect(url_for("my_profile"))
        
    else:
        friend = conn.execute("SELECT * FROM customer WHERE phone_num = %s", friend_phone).fetchone()
        if friend is None:
            return render_template_string('<html><head></head><body>The person you are looking '\
                                          'for is not registered. <a href="/myprofile">'\
                                     '<button>Go Back</button></a></body><html>')
        else:
            friend_id = friend.customer_id
            if ((conn.execute("SELECT customer_id_1 FROM friend_request WHERE customer_id_1 = %s AND " \
                "customer_id_2 = %s", uid, friend_id).fetchone() is None) and (conn.execute("SELECT customer_id_1 FROM friend_request WHERE customer_id_1 = %s AND " \
                "customer_id_2 = %s", friend_id, uid).fetchone() is None)):      
                conn.execute("INSERT INTO friend_request VALUES (%s, %s,'pending');", uid, friend_id)
                return render_template_string('<html><head></head><body>Request successfully sent! '\
                                              '<a href="/myprofile">'\
                                              '<button>Go Back</button></a></body><html>')
                
            else:        
                return render_template_string('<html><head></head><body>There is already a request! '\
                                              '<a href="/myprofile">'\
                                              '<button>Go Back</button></a></body><html>')
                
        
# =============================================================================
# Restaurant Specific Functions
# =============================================================================

@app.route('/restaurant/<res_id>', methods =['GET'])
def restaurant(res_id):
    conn=g.conn
    #array-like res
    res=conn.execute('select * from restaurant where res_id=%s;',(res_id,)).fetchone()
    reviews=conn.execute('SELECT rati.rating_id rating_id, text, likes, rati.stars_value stars_value '\
                         'FROM restaurant res, rating rati, review rev '\
                        'where res.res_id=%s AND res.res_id=rati.res_id '\
                        ' AND rati.rating_id=rev.rating_id order by likes desc;',(res_id,))
    all_reviews=[]
    for r in reviews:
        r_dict=dict(r)
        all_reviews.append(r_dict)

    city_state=conn.execute('SELECT * from city where city_id=%s',(res['city_id'],)).fetchone()
    print(city_state)
    city_state=city_state['city_name']+' '+ city_state['state_abbrev']
    context=dict(res=res,city_state=city_state,reviews=all_reviews) 

    return render_template('restaurant.html', **context)



@app.route('/likereview/<res_id>/<rating_id>', methods =['GET'])
@customer_login_required
def likereview(res_id,rating_id):
    conn=g.conn
    customer_id=g.user_id
    if (conn.execute('SELECT * from likes_review WHERE rating_id=%s AND customer_id=%s',
                     (rating_id,customer_id)).fetchone() is None) :
        conn.execute('INSERT INTO likes_review VALUES (%s,%s)',(rating_id,customer_id))
        conn.execute("UPDATE review SET likes=likes+1 WHERE rating_id=%s",(rating_id,))
        return redirect(url_for('restaurant',res_id=res_id))
    else:
        return render_template_string('<html><head></head><body>You liked it already</body><html>')


@app.route('/reservation/<res_id>', methods =['GET','POST'])
@customer_login_required
def reserve(res_id):    
    conn=g.conn
    customer_id=g.user_id
    context=dict(res_id=res_id)
    if request.method=='POST':
        reserv_id=shortuuid.uuid()
        guest_num=request.form["guest_num"]
        datetime=request.form['datetime']
        customer_id=g.user_id
        acceptance='pending'
        conn.execute("INSERT INTO reservation VALUES (%s,%s,%s,%s,%s,%s)",
                     reserv_id,guest_num,datetime,customer_id,res_id,acceptance)
        
        return render_template('revdone.html',**context)
    
    return render_template('reservation.html', **context)
    


# Example of adding new data to the database
'''
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()
'''

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
