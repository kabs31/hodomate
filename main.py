from pathlib import PosixPath
from sqlite3.dbapi2 import Cursor, connect
from flask import Flask,render_template,request,redirect,session,url_for
import sqlite3
from PIL import Image
from datetime import date


app = Flask(__name__)
app.secret_key = "helo"
app.config['UPLOAD_DIR']='static'

con=sqlite3.connect('hodomate.db')
con.execute("create table if not exists cposts(postid integer primary key,username text,postdate text,description text,imgname text,imgblob blob,likes integer,location text)")
con.execute("create table if not exists likes(likeid integer primary key,username text,postid integer)")
con.execute("create table if not exists comments(commentid integer primary key,pid integer,username text,comment text,date text)")
con.close()




@app.route("/")
@app.route("/home",methods=['GET','POST'])
def home():
       if 'user' in session:
          if(request.method=='POST'):                     #FILTER POST REQUEST
              filters = request.form.getlist('filter')
              location=request.form['location']
              print(filters,location)
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
          
@app.route("/myprofile",methods=['GET','POST'])
def myprofile():
    if(request.method=='POST'):
        description=request.form['description']
        location=request.form['location']
        image=request.files['files']
        imgname=image.filename
        imgblob=image.read()
        tdydate=str(getdate())
        writeTostatic(imgblob,imgname)     #writes the image to the static/postimages folder
        resizeimg(imgname)                        #resizes img to 250*917 px
        con = sqlite3.connect('hodomate.db')
        cur = con.cursor()
        cur.execute("INSERT INTO cposts(username,postdate,description,imgname,imgblob,likes,location) values(?,?,?,?,?,?,?)",(session['user'],tdydate,description,imgname,imgblob,0,location))
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
         cur.close()
         con.close() 
         return redirect(url_for('myprofile'))


def writeTostatic(data,filename):
    imgpath="D:/college/flask project/web demo/Hodomate/static/postimages/"+str(filename)
    with open(imgpath,'wb') as file:
        file.write(data)

def resizeimg(imgname):
    imgpath="D:/college/flask project/web demo/Hodomate/static/postimages/"+str(imgname)
    im=Image.open(imgpath)
    im=im.resize((917,250))
    im.save(imgpath)

def getdate():
    today = date.today()
    d1 = today.strftime("%d-%m-%Y")
    return d1


app.run(debug=True)     
  