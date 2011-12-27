import os, cgi, logging, hashlib
from datetime import datetime
from google.appengine.api import users, xmpp, mail
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app

from src.settings import *


class User(db.Model):
    user = db.UserProperty(required=True)
    active = db.BooleanProperty(default=False)
    accactivationcode = db.StringProperty()

class MainPage(webapp.RequestHandler):
    def get(self):
        """ handles the welcome page. """
        user = users.get_current_user()

        template_values = {
            'user': user,
            'isadmin': users.is_current_user_admin(),
            'loginurl': users.create_login_url(self.request.uri),
            'logouturl': users.create_logout_url('/'),
        }
        template_path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
        self.response.out.write(template.render(template_path, template_values, debug=True))
    
    def post(self):
        """ handles the subscription/invitation to the application """
        user_address = self.request.get("email_address")
        user, code = users.User(user_address), self.confirmationUrl(user_address)        
        
        user = User(user=user, accactivationcode=code, active=False)
        user.put()
        
        try:
            self.shoot_welcome_mail(user_address)
        except:
            pass
        
        try:
            self.invite_chat_bot(user_address)
        except:
            pass
        
        template_values = {
             'user_address' : user_address
        }
        template_path = os.path.join(os.path.dirname(__file__), '../templates/subscribe.html')
        self.response.out.write(template.render(template_path, template_values, debug=True))
        
    def confirmationUrl(self, body):
        return hashlib.md5(body).hexdigest()
    
    def invite_chat_bot(self, user_address):
        """ send invite to the chat list"""
        xmpp.send_invite(user_address, GTALK_ID)
        
    def shoot_welcome_mail(self, user_address):
        sender_address = EMAILID_WELCOME
        subject = EMAIL_WELCOME_SUBJECT
        body = EMAIL_WELCOME_BODY % self.confirmationUrl(user_address)
                
        """ shoot the invitation mail. """
        mail.send_mail(sender_address, user_address, subject, body)
    
class HelpPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        template_path = os.path.join(os.path.dirname(__file__), '../templates/help.html')
        self.response.out.write(template.render(template_path, template_values, debug=True))
    
class AboutPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        template_path = os.path.join(os.path.dirname(__file__), '../templates/about.html')
        self.response.out.write(template.render(template_path, template_values, debug=True))
    
class ActivatePage(webapp.RequestHandler):
    def get(self, code):
        query = User.all()
        query.filter('accactivationcode =', code)
        
        user = query.fetch(1)[0]
        user.active = True
        user.put()
        
        template_values = {}
        template_path = os.path.join(os.path.dirname(__file__), '../templates/activate.html')
        self.response.out.write(template.render(template_path, template_values, debug=True))
    
application = webapp.WSGIApplication([('/', MainPage),
                                      ('/help', HelpPage),
                                      ('/about', AboutPage),
                                      ('/activate/(.*)', ActivatePage),
                                      ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(application)
