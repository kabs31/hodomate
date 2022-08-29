from pathlib import PosixPath
from sqlite3.dbapi2 import Cursor, connect
from flask import Flask,render_template,request,redirect,session,url_for
import sqlite3
from PIL import Image
from datetime import date
from recommend import recommendUser
from geopy.geocoders import Nominatim
from TravelSalesman import fetchTravelPattern
geolocator = Nominatim(user_agent="geoapiExercises")



app = Flask(__name__)
app.secret_key = "helo"
app.config['UPLOAD_DIR']='static'

con=sqlite3.connect('hodomate.db')
con.execute("create table if not exists cposts(postid integer primary key,username text,postdate text,description text,imgname text,imgblob blob,likes integer,location text,latitude real,longitude real);")
con.execute("create table if not exists likes(likeid integer primary key,username text,postid integer);")
con.execute("create table if not exists comments(commentid integer primary key,pid integer,username text,comment text,date text);")
con.execute("create table if not exists planlist(planid integer primary key,username text,planname text);")
con.execute("create table if not exists planpost(planpostno integer primary key,planid integer,postid integer);")
con.close()




@app.route("/")
@app.route("/home",methods=['GET','POST'])
def home():
       if 'user' in session:
          if(request.method=='POST'):                     #FILTER POST REQUEST
              filters = request.form.getlist('filter')
              location=request.form['location']
              if(len(filters)==1):                          #FOR SINGLE FILTERS
                  if('1' in filters):                                   #FOR LIKE FILTER
                    if(location!='0'):
                       con = sqlite3.connect('hodomate.db')
                       cur = con.cursor()
                       cur.execute(f"SELECT * FROM cposts WHERE LOWER(location) LIKE '%{location}%' ORDER BY likes desc;")
                       data=cur.fetchall()
                       cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                       comments=cur.fetchall()
                       cur.close()
                       con.close()
                       return render_template("home.html",u=session['user'],data=data,comments=comments) 
                    else:     
                      con = sqlite3.connect('hodomate.db')
                      cur = con.cursor()
                      cur.execute(f"SELECT * FROM cposts ORDER BY likes desc;")
                      data=cur.fetchall()
                      cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                      comments=cur.fetchall()
                      cur.close()
                      con.close()
                      return render_template("home.html",u=session['user'],data=data,comments=comments)
                  elif('2' in filters):                         #FOR RECNET FILTER
                    if(location!='0'):  
                      con = sqlite3.connect('hodomate.db')
                      cur = con.cursor()
                      cur.execute(f"SELECT * FROM cposts WHERE LOWER(location) LIKE '%{location}%' ORDER BY postdate desc;")
                      data=cur.fetchall()
                      cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                      comments=cur.fetchall()
                      cur.close()
                      con.close()
                      return render_template("home.html",u=session['user'],data=data,comments=comments) 
                    else:
                      con = sqlite3.connect('hodomate.db')
                      cur = con.cursor()
                      cur.execute(f"SELECT * FROM cposts ORDER BY postdate desc;")
                      data=cur.fetchall()
                      cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                      comments=cur.fetchall()
                      cur.close()
                      con.close()
                      return render_template("home.html",u=session['user'],data=data,comments=comments) 
              elif(len(filters)==2):                      #FOR BOTH THE FILTERS
                      if(location!='0'):
                          con = sqlite3.connect('hodomate.db')
                          cur = con.cursor()
                          cur.execute(f"SELECT * FROM cposts WHERE LOWER(location) LIKE '%{location}%' ORDER BY postdate desc,likes desc;")
                          data=cur.fetchall()
                          cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                          comments=cur.fetchall()
                          cur.close()
                          con.close()
                          return render_template("home.html",u=session['user'],data=data,comments=comments)
                      else:
                          con = sqlite3.connect('hodomate.db')
                          cur = con.cursor()
                          cur.execute(f"SELECT * FROM cposts ORDER BY postdate desc,likes desc;")
                          data=cur.fetchall()
                          cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                          comments=cur.fetchall()
                          cur.close()
                          con.close()
                          return render_template("home.html",u=session['user'],data=data,comments=comments)
              elif(len(filters)==0 and location!='0'):          #FOR LOCATION FILTER ALONE
                  con = sqlite3.connect('hodomate.db')
                  cur = con.cursor()
                  cur.execute(f"SELECT * FROM cposts WHERE LOWER(location) LIKE '%{location}%';")
                  data=cur.fetchall()
                  cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                  comments=cur.fetchall()
                  cur.close()
                  con.close()
                  return render_template("home.html",u=session['user'],data=data,comments=comments)

          else:                                      #NORMAL GET REQUEST
                con = sqlite3.connect('hodomate.db')
                cur = con.cursor()
                cur.execute(f"SELECT * FROM cposts;")
                data=cur.fetchall()
                cur.execute(f"SELECT * FROM comments ORDER BY pid;")
                comments=cur.fetchall()
                cur.close()
                con.close()
                return render_template("home.html",u=session['user'],data=data,comments=comments)
            
       else:
            return redirect(url_for("login"))

@app.route("/recommendation",methods=['GET','POST'])
def recommendation():
    if 'user' in session:
        result=[]
        con = sqlite3.connect('hodomate.db')
        cur = con.cursor()
        cur.execute(f"SELECT * FROM likes where username='{session['user']}';")
        data=cur.fetchall()
        result=recommendUser(data)     
        cur.execute(f"SELECT * FROM comments ORDER BY pid;")
        comments=cur.fetchall()
        cur.close()
        con.close()
        return render_template("recommendation.html",u=session['user'],data=result,comments=comments)
    else:
            return redirect(url_for("login"))    

@app.route("/myprofile",methods=['GET','POST'])
def myprofile():
    if(request.method=='POST'):
        description=request.form['description']
        latitude=request.form['latitude']
        longitude=request.form['longitude']
        address = getAddress(latitude,longitude)
        image=request.files['files']
        imgname=image.filename
        imgblob=image.read()
        tdydate=str(getdate())
        writeTostatic(imgblob,imgname)     #writes the image to the static/postimages folder
        resizeimg(imgname)                        #resizes img to 250*917 px
        con = sqlite3.connect('hodomate.db')
        cur = con.cursor()
        cur.execute("INSERT INTO cposts(username,postdate,description,imgname,imgblob,likes,location,latitude,longitude) values(?,?,?,?,?,?,?,?,?)",(session['user'],tdydate,description,imgname,imgblob,0,address,latitude,longitude))
        con.commit()
        cur.execute(f"SELECT * FROM cposts WHERE username='{session['user']}';")
        data=cur.fetchall()
        cur.close()
        con.close()
        return render_template("myprofile.html",data=data)
    else:
       if 'user' in session:
           con = sqlite3.connect('hodomate.db')
           cur = con.cursor()
           cur.execute(f"SELECT * FROM cposts WHERE username='{session['user']}';")
           data=cur.fetchall()
           cur.execute(f"SELECT * FROM comments ORDER BY pid;")
           comments=cur.fetchall()
           cur.close()
           con.close()
           return render_template("myprofile.html",data=data,comments=comments)
       else:
          return redirect(url_for("login"))

@app.route("/viewmyplans",methods=['GET','POST'])
def viewmyplans():
    if 'user' in session:
        if(request.method=='POST'):
            planname = request.form['planname']
            con = sqlite3.connect('hodomate.db')
            cur = con.cursor()
            cur.execute("INSERT INTO planlist(username,planname) values(?,?)",(session['user'],planname))
            con.commit()
            cur.execute(f"select * from planlist where username='{session['user']}';")
            data = cur.fetchall()
            cur.close()
            con.close()
            return render_template("ViewMyPlans.html",data=data)
        else:    
            con = sqlite3.connect('hodomate.db')
            cur = con.cursor()
            cur.execute(f"select * from planlist where username='{session['user']}';")
            data = cur.fetchall()
            cur.close()
            con.close()
            return render_template("ViewMyPlans.html",data=data)
    else:
       return redirect(url_for("login"))

@app.route("/viewplanposts",methods=['GET','POST'])
def viewplanposts():      
    if 'user' in session:
        if(request.method=='POST'):
            planid = request.form['planid']
            con = sqlite3.connect('hodomate.db')
            cur = con.cursor()
            cur.execute(f"select cp.postid,cp.username,cp.postdate,cp.description,cp.imgname,cp.imgblob,cp.likes,cp.location from planpost as pp join cposts as cp on pp.postid=cp.postid where planid='{planid}';")
            data = cur.fetchall()
            cur.execute(f"select planname from planlist where planid='{planid}';")
            planname = cur.fetchone()
            planname = planname[0]
            cur.execute(f"SELECT * FROM comments ORDER BY pid;")
            comments=cur.fetchall()
            cur.close()
            con.close()
            return render_template("viewplanposts.html",planid=planid,planname=planname,data=data,comments=comments)
    else:
       return redirect(url_for("login"))


@app.route("/travelallplan",methods=['GET','POST'])
def travelallplan():      
    if 'user' in session:
        if(request.method=='POST'):
            planid = request.form['planid']
            con = sqlite3.connect('hodomate.db')
            cur = con.cursor()
            cur.execute(f"select cp.postid,cp.latitude,cp.longitude from planpost as pp join cposts as cp on pp.postid=cp.postid where planid='{planid}';")
            data = cur.fetchall()
            posts=[]
            travelpattern=fetchTravelPattern(data)
            for path in travelpattern:
                cur.execute(f"select * from cposts where postid='{path}';")
                posts.append(cur.fetchone())    
            cur.close()
            con.close()
            return render_template("optimizedRoute.html",data=posts)
    else:
       return redirect(url_for("login"))


@app.route("/addtoplan",methods=['GET','POST'])
def addtoplan():
    if 'user' in session:
        if(request.method=='POST'):
            pid = request.form['add']
            con = sqlite3.connect('hodomate.db')
            cur = con.cursor()
            cur.execute(f"select * from planlist where username='{session['user']}';")
            data = cur.fetchall()
            cur.close()
            con.close()
            return render_template("addtoplan.html",data=data,pid=pid)
    else:
       return redirect(url_for("login"))     

@app.route("/addhere",methods=['GET','POST'])
def addhere():    
    if 'user' in session:
        if(request.method=='POST'):
            pid = request.form['pid']
            planid = request.form['addhere']
            con = sqlite3.connect('hodomate.db')
            cur = con.cursor()
            cur.execute("INSERT INTO planpost(planid,postid) values(?,?)",(planid,pid))
            con.commit()
            cur.close()
            con.close()
            return redirect(url_for("home"))
    else:
       return redirect(url_for("login"))

@app.route("/login",methods=['POST','GET'])
def login():
    if(request.method=='POST'):
        username = request.form["username"]
        password = request.form["password"]
        con=sqlite3.connect("hodomate.db")
        con.row_factory=sqlite3.Row
        cur=con.cursor()
        cur.execute("select * from user where username=? and password=?",(username,password))
        data=cur.fetchone()
        cur.close()
        con.close()
        if data:                                              #checking whether user is registered
            session['user']=username
            return redirect(url_for('home'))
        else:
            msg="Incorrect details or Register to start!"
            return render_template("login.html",msg=msg)    
    else:
      return render_template("login.html")    

@app.route("/register",methods=['GET','POST'])
def register():
    if(request.method=='POST'):
        username=request.form['uname']
        email=request.form['email']
        password=request.form['passw']
        con=sqlite3.connect("hodomate.db")
        con.row_factory=sqlite3.Row
        cur=con.cursor()
        statement=f"select * from user where username='{username}';"
        cur.execute(statement)
        data=cur.fetchone()
        if data:                                             #checking whether username already exists
            msg="Username already exists!"
            return render_template("register.html",msg=msg)
        else:    
           cur.execute("insert into user(username,email,password) values(?,?,?)",(username,email,password))
           con.commit()
           cur.close()
           con.close()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    if(session):
     user = session.pop('user')
     return render_template("logout.html",user=user)
    else:
       return redirect(url_for("login"))    

@app.route("/myprofilelike",methods=['POST'])
def myprofilelike():
       if(request.method=='POST'):
           pid=request.form['like']
           con = sqlite3.connect('hodomate.db')
           con.row_factory=sqlite3.Row
           cur = con.cursor()
           cur.execute("SELECT * FROM likes WHERE username=? and postid=?",(session['user'],pid))
           data=cur.fetchone()
           if data:
               cur.execute("DELETE FROM likes WHERE username=? and postid=?",(session['user'],pid))
               con.commit()
               cur.execute("UPDATE cposts SET likes=likes-1 WHERE postid=?;",(pid))
               con.commit()
               cur.close()
               con.close() 
               return redirect(url_for('myprofile'))  
           else:    
               cur.execute("INSERT INTO likes(username,postid) values(?,?)",(session['user'],pid))
               con.commit()
               cur.execute("UPDATE cposts SET likes=likes+1 WHERE postid=?;",(pid))
               con.commit()
               cur.close()
               con.close()             
               return redirect(url_for('myprofile'))    


@app.route("/homelike",methods=['POST'])
def homelike():
       if(request.method=='POST'):
           pid=request.form['like']
           con = sqlite3.connect('hodomate.db')
           con.row_factory=sqlite3.Row
           cur = con.cursor()
           cur.execute("SELECT * FROM likes WHERE username=? and postid=?",(session['user'],pid))
           data=cur.fetchone()
           if data:
               cur.execute("DELETE FROM likes WHERE username=? and postid=?",(session['user'],pid))
               con.commit()
               cur.execute("UPDATE cposts SET likes=likes-1 WHERE postid=?",(pid))
               con.commit()
               cur.close()
               con.close() 
               return redirect(url_for('home'))  
           else:    
               cur.execute("INSERT INTO likes(username,postid) values(?,?)",(session['user'],pid))
               con.commit()
               cur.execute("UPDATE cposts SET likes=likes+1 WHERE postid=?",(pid))
               con.commit()
               cur.close()
               con.close()             
               return redirect(url_for('home'))    

@app.route("/addcomment",methods=['POST'])
def comment():
       if(request.method=='POST'):
           pid=request.form['cbutton']
           page=request.form['page']
           comment=request.form['comment']
           date=getdate()
           con=sqlite3.connect('hodomate.db')
           cur=con.cursor()
           cur.execute("INSERT INTO comments(pid,username,comment,date) VALUES(?,?,?,?)",(pid,session['user'],comment,date))
           con.commit()
           cur.close()
           con.close()
           return redirect(url_for(page))            


@app.route("/edit",methods=['POST'])   
def edit():
    if(request.method=='POST'):
         pid=request.form['edit']
         return render_template("PostUpdate.html",pid=pid)

@app.route("/update",methods=['POST'])   
def update():
    if(request.method=='POST'):
         pid=request.form['pid']
         description=request.form['description']
         location=request.form['location']
         image=request.files['files']
         imgname=image.filename
         tdydate=str(getdate())
         print(pid,description,location,imgname)
         if(len(description)!=0 and len(location)==0 and len(imgname)==0):
             con = sqlite3.connect('hodomate.db')
             cur = con.cursor()
             cur.execute("UPDATE cposts SET description=?,postdate=? WHERE postid=? ",(description,tdydate,pid))
             con.commit()
             cur.close()
             con.close()
             return redirect(url_for('myprofile'))
         elif(len(description)==0 and len(location)!=0 and len(imgname)==0):
             con = sqlite3.connect('hodomate.db')
             cur = con.cursor()
             cur.execute("UPDATE cposts SET location=?,postdate=? WHERE postid=? ",(location,tdydate,pid))
             con.commit()
             cur.close()
             con.close()
             return redirect(url_for('myprofile')) 
         elif(len(description)==0 and len(location)==0 and len(imgname)!=0):
             imgblob=image.read()
             writeTostatic(imgblob,imgname)     #writes the image to the static/postimages folder
             resizeimg(imgname)                   #resizes img to 250*917 px
             con = sqlite3.connect('hodomate.db')
             cur = con.cursor()
             cur.execute("UPDATE cposts SET imgname=?,imgblob=?,postdate=? WHERE postid=? ",(imgname,imgblob,tdydate,pid))
             con.commit()
             cur.close()
             con.close()
             return redirect(url_for('myprofile')) 
         elif(len(description)!=0 and len(location)!=0 and len(imgname)==0):
             con = sqlite3.connect('hodomate.db')
             cur = con.cursor()
             cur.execute("UPDATE cposts SET description=?,location=?,postdate=? WHERE postid=? ",(description,location,tdydate,pid))
             con.commit()
             cur.close()
             con.close()
             return redirect(url_for('myprofile')) 
         elif(len(description)!=0 and len(location)==0 and len(imgname)!=0):
             imgblob=image.read()
             writeTostatic(imgblob,imgname)     #writes the image to the static/postimages folder
             resizeimg(imgname) 
             con = sqlite3.connect('hodomate.db')
             cur = con.cursor()
             cur.execute("UPDATE cposts SET description=?,imgname=?,imgblob=?,postdate=? WHERE postid=? ",(description,imgname,imgblob,tdydate,pid))
             con.commit()
             cur.close()
             con.close()
             return redirect(url_for('myprofile'))   
         elif(len(description)==0 and len(location)!=0 and len(imgname)!=0):
             imgblob=image.read()
             writeTostatic(imgblob,imgname)     #writes the image to the static/postimages folder
             resizeimg(imgname) 
             con = sqlite3.connect('hodomate.db')
             cur = con.cursor()
             cur.execute("UPDATE cposts SET location=?,imgname=?,imgblob=?,postdate=? WHERE postid=? ",(location,imgname,imgblob,tdydate,pid))
             con.commit()
             cur.close()
             con.close()
             return redirect(url_for('myprofile'))                   
         else: 
             return  redirect(url_for('myprofile'))


@app.route("/myprofiledelete",methods=['POST'])   
def myprofiledelete():
    if(request.method=='POST'):
         pid=request.form['delete']
         con = sqlite3.connect('hodomate.db')
         cur = con.cursor()
         cur.execute("DELETE FROM cposts WHERE postid=?",(pid))
         con.commit()
         cur.execute("DELETE FROM likes WHERE postid=?",(pid))
         con.commit()
         cur.close()
         con.close() 
         return redirect(url_for('myprofile'))

@app.route("/bookcab",methods=['POST'])
def bookcab():
    if(request.method=='POST'):
        pid=request.form['book']
        con = sqlite3.connect('hodomate.db')
        cur = con.cursor()
        cur.execute("select * from cposts where postid=?",(pid))
        data = cur.fetchone()
        cur.close()
        con.close()
        latitude = data[8]
        longitude = data[9]
        deeplink="http://book.olacabs.com/?utm_source=12343&dsw=yes&"
        deeplink+="drop_lat="+str(latitude)+"&"
        deeplink+="drop_lng="+str(longitude)
        return redirect(deeplink)
        

def writeTostatic(data,filename):
    imgpath="static/postimages/"+str(filename)
    with open(imgpath,'wb') as file:
        file.write(data)

def resizeimg(imgname):
    imgpath="static/postimages/"+str(imgname)
    im=Image.open(imgpath)
    im=im.resize((917,250))
    im.save(imgpath)

def getdate():
    today = date.today()
    d1 = today.strftime("%d-%m-%Y")
    return d1

def getAddress(latitude,longitude):
    location = geolocator.reverse(latitude+","+longitude)
    address = location.raw['address']
    suburb = address.get('suburb', '')
    city = address.get('city', '')
    state = address.get('state', '')
    country = address.get('country', '')
    zipcode = address.get('postcode')
    return suburb+" "+city+" "+state+" "+country+" "+zipcode

app.run(debug=True)     
  