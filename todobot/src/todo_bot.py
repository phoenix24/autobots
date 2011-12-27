import os, cgi, logging, hashlib, re
from datetime import datetime
from google.appengine.api import users, xmpp, mail
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson
from src.main import User
from src.settings import *

class Todo(User):
    task = db.StringProperty(required=True, multiline=True)
    date = db.DateTimeProperty(required=True, auto_now_add=True)
    status = db.StringProperty(required=True, choices=set(["incomplete", "complete", "on-going"]))
    
class TodosPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        query = Todo.all().filter('user =', user).order('-date')
        
        todos = query.fetch(100) if user else []

        template_values = {
            'user': user,
            'todos': todos,
            'isadmin': users.is_current_user_admin(),
            'loginurl': users.create_login_url(self.request.uri),
            'logouturl': users.create_logout_url('/'),
        }
        template_path = os.path.join(os.path.dirname(__file__), '../templates/todos.html')
        self.response.out.write(template.render(template_path, template_values, debug=True))
        
    def post(self):
        user = users.get_current_user()
        
        if user and self.request.get('task-action') == 'new':
            todo = Todo(user=user, task=self.request.get('task'), status=self.request.get('status'))
            todo.put()
            
        if user and self.request.get('task-action') == 'delete':
            todo = db.get(db.Key(self.request.get('task-key')))
            todo.delete()
            
        if user and self.request.get('task-action') == 'update':
            todo = db.get(db.Key(self.request.get('task-key')))
            todo.status = self.request.get('status')
            todo.put()
            
        self.redirect('/todos')


class XMPPHandler(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        logging.info("received the incoming chat message : " + message.sender)
        try:
            sender = message.sender[:message.sender.index("/")]
        except:
            sender = message.sender
             
        action  = message.body[0:4]
        body    = message.body[4:]

        sender  = users.User(sender)
        
        if action.lower() == 'task':
            todo = Todo(user=sender, task=body, status="incomplete")
            todo.put()
            message.reply("hey, task added!!")
            
        elif action.lower() == 'list':
            query = Todo.all().filter('user =', sender).order('-date')
            todos = query.fetch(100)
            
            for todo in todos:
                message.reply(todo.task + ", " + todo.status)
        else:
            message.reply("yello! (hit 'HELP')")

    
class EmailHandler(InboundMailHandler):
    def receive(self, mail_message):
        mailsrch = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
        original_sender = mail_message.sender
        
        """ monkey patch hack! 
            otherwsise for the incoming email addresses such as ("some user" <some.user@example.com>),
            it takes the user to be : "some user" <some.user@example.com>
            instead of : some.user@example.com
            @todo, need to find an appropriate fix!
        """
        parsed_sender = mailsrch.findall(original_sender)[0]
        logging.info("Parsed email-address :" + original_sender + ", " + parsed_sender)
        
        sender = users.User(parsed_sender)

        html_bodies = mail_message.bodies('text/html')
        plaintext_bodies = mail_message.bodies('text/plain')
        
        for content_type, body in html_bodies:
            decoded_html = body.decode()
            
        for content_type, body in plaintext_bodies:
            decoded_plaintext = body.decode()
            
        task_body = decoded_plaintext or decoded_html or "failed to parse the task"

        logging.info("Recieved an email : " + task_body)
        todo = Todo(user=sender, task=task_body, status="incomplete")
        todo.put()

        mail.send_mail(EMAILID_TASK, mail_message.sender, EMAIL_TASK_RECEIVED_ADDED_SUBJECT, EMAIL_TASK_RECEIVED_ADDED_BODY)
        

class SMSHandler(webapp.RequestHandler):
    def get(self):
         content = self.request.get("content")
         phonenumber = self.request.get("msisd")
         template_values = {
            "content" : content,
            "phonenumber" : phonenumber,
            "ip_address_is" : self.request.remote_addr
         }
#        template_path = os.path.join(os.path.dirname(__file__), '../templates/help.html')
#        self.response.out.write(template.render(template_path, template_values, debug=True))
         self.response.out.write(simplejson.dumps(template_values))

application = webapp.WSGIApplication([(r'/todos', TodosPage),
                                      (r'/sms', SMSHandler),
                                      (r'/_ah/xmpp/message/chat/', XMPPHandler),
                                      EmailHandler.mapping(),
                                      #(r'/_ah/mail/task@todo-bot.appspotmail.com',  EmailHandler),
                                      ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(application)
