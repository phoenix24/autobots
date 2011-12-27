import os, cgi, logging, urllib2
from datetime import datetime
from google.appengine.api import xmpp, mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


from django.utils import simplejson

#import application settings,
from src.settings import *

class GitHubNoticeXMPP(webapp.RequestHandler):
    def post(self, emailid):

        #need to add email validation.
        user_address = urllib2.unquote(emailid)
        
        try:
            commitmessages = ''
            payload = self.request.get('payload')
            payload = simplejson.loads(payload)
        
            for commit in payload['commits']:
                commitmessages += commit['author']['name'] + ': ' + commit['message'] + '\n'
            
            msg = '\n' + payload['repository']['url'] + '\n' + commitmessages

            """ shoot the notification to chat-bot """
            xmpp.send_message(user_address, msg)

        except:
            xmpp.send_message(user_address, "another commit on a project you are listening to; but failed to parse details")
            pass

class GitHubNoticeEmail(webapp.RequestHandler):
    def post(self, emailid):
	try:
            #need to add email validation.
            user_address = urllib2.unquote(emailid)
            sender_address = EMAILID_NOTICE

            commitmessages = ''
            payload = self.request.get('payload')
            payload = simplejson.loads(payload)
        
            for commit in payload['commits']:
                commitmessages += commit['author']['name'] + ': ' + commit['message'] + '\n'
            
            subject = EMAILID_NOTICE_SUBJECT % payload['repository']['name']
            body = EMAILID_NOTICE_BODY % (payload['repository']['name'], commitmessages)
  
            """ shoot the notification mail. """
            mail.send_mail(sender_address, user_address, subject, body)

	except:
	    logging.info("error occured while sending email. %s" % datetime.now() )	
	    pass

class GitHubClusterEmail(webapp.RequestHandler):
    def post(self, emailid):
	try:
            #need to add email validation.
            user_address = urllib2.unquote(emailid)
            sender_address = EMAILID_NOTICE

            time = self.request.get('time')
            cluster = self.request.get('cluster')
            message = self.request.get('message')
        
            subject = EMAILID_NOTICE_SUBJECT % cluster
            body = EMAILID_NOTICE_BODY % ( time, message )
  
            """ shoot the notification mail. """
            mail.send_mail(sender_address, user_address, subject, body)

	except:
	    logging.info("error occured while sending email. %s" % datetime.now() )	
	    pass


application = webapp.WSGIApplication([
        (r'/notice/email/(.*)', GitHubNoticeEmail),
        (r'/notice/cluster/(.*)', GitHubClusterEmail),
        (r'/notice/xmpp/(.*)', GitHubNoticeXMPP),
        (r'/notice/(.*)', GitHubNoticeXMPP),], debug=True)

if __name__ == "__main__":
    run_wsgi_app(application)
