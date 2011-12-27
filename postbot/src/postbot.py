import os, cgi, logging, urllib2
from google.appengine.api import xmpp, mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

#import application settings
from src.settings import *

class HTTPBot(webapp.RequestHandler):
    def parsedata(self):
        #need to add email validation.
        self.user_address = urllib2.unquote(self.request.get('email'))
        self.subject = self.request.get('subject')
        self.payload = self.request.get('payload')
        self.service = self.request.get('service')
        print "service is ", self.service

    def sendmail(self):
        """ shoot the notification mail. """
        mail.send_mail(EMAILID_NOTICE, self.user_address, self.subject, self.payload)

    def sendxmpp(self):
        """ shoot the notification mail. """
        xmpp.send_message(self.user_address, self.payload)

    def domagic(self):
        try:
            #need to get all the posted data.
            self.parsedata()
            self.sendmail() if self.service == "email" else ''
            self.sendxmpp() if self.service == "xmpp" else ''
        except:
            logging.info("oopsis! error while parsing the arguments.")

    def get(self):
        self.domagic()

    def post(self):
        self.domagic()

application = webapp.WSGIApplication([ (r'/bot', HTTPBot), ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(application)


