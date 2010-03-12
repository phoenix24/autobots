package controllers;
import com.google.appengine.api.xmpp.JID;
import com.google.appengine.api.xmpp.Message;
import com.google.appengine.api.xmpp.MessageBuilder;
import com.google.appengine.api.xmpp.SendResponse;
import com.google.appengine.api.xmpp.XMPPService;
import com.google.appengine.api.xmpp.XMPPServiceFactory;


import play.mvc.*;

public class Application extends Controller {

    public static void index() {

        JID jid = new JID("gopi.daiict@gmail.com");
        String msgBody = "this is a test message gopi! chill :D";
        Message msg = new MessageBuilder()
            .withRecipientJids(jid)
            .withBody(msgBody)
            .build();
                
        boolean messageSent = false;
        XMPPService xmpp = XMPPServiceFactory.getXMPPService();
        if (xmpp.getPresence(jid).isAvailable()) {
            SendResponse status = xmpp.sendMessage(msg);
            messageSent = (status.getStatusMap().get(jid) == SendResponse.Status.SUCCESS);
        }

        if (!messageSent) {
            // Send an email message instead...
        }

        render();
    }

    public static void invite() {
	JID jid = new JID("gopi.daiict@gmail.com");
	XMPPService xmpp = XMPPServiceFactory.getXMPPService();
	xmpp.sendInvitation(jid);

	render();
    }

}
