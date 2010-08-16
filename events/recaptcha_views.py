from django.contrib.comments.views.comments import post_free_comment
from django.http import Http404
import captcha
import settings

def free_comment_wrapper( request, extra_context = {}, context_processors = None ):
    if request.POST:
        check_captcha = captcha.submit( request.POST.get( 'recaptcha_challenge_field', '' ),
               request.POST.get( 'recaptcha_response_field', '' ), settings.RECAPTCHA_PRIVATE_KEY,
               request.META['REMOTE_ADDR'] )
        if check_captcha.is_valid is False:
            raise Http404, "Invalid Captcha Attempt"
        extra_context["recaptcha_html"] = captcha.displayhtml( settings.RECAPTCHA_PUB_KEY )
        return post_free_comment( request, extra_context, context_processors )
    raise Http404, "Only POSTs are allowed"

# This is a wrapper around post_free_comment, so preempt it in urls.py

#    ( r'^comments/postfree/$', 'recaptcha_views.free_comment_wrapper' ),
#    ( r'^comments/', include( 'django.contrib.comments.urls.comments' ) ),

# Now, to deal with the security, I needed a special template tag to generate the hash

#from django.contrib.comments.models import Comment
#from django.contrib.contenttypes.models import ContentType
#
#def comment_security_hash( blogentry, opts ):
#    targ = '%s:%s' % ( ContentType.objects.get_for_model( blogentry ).id, blogentry.id )
#    return {"hash":Comment.objects.get_security_hash( opts, '', '', targ )}

#register.inclusion_tag( "blog/templatetags/comment_security_hash.html" )( comment_security_hash )

# I wanted this to work with a generic detail view, so here is mine
# (setup for the model "BlogEntry" in "blogs").

#  ( r'^blog/(?P<slug>[\w-]+)/$$', 'django.views.generic.list_detail.object_detail', {'queryset':BlogEntry.objects.public(), 'slug_field':'slug', "extra_context":{"recaptcha_html":captcha.displayhtml( settings.RECAPTCHA_PUB_KEY ), "contenttype_id":ContentType.objects.get( app_label__exact = "blog", model__exact = "blogentry" ).id}} ),

# It is Really messy, but I use extra_context to get recaptcha_html 
# (the iframe) and then i pass  in the contettype_id to build the target input field.

# Finally, in the template code, we have to build a custom comment form.

#         < form action = "/comments/postfree/" method = "post" >
#                < p >< label for = "id_person_name" > Your name: </ label > < input type = "text" id = "id_person_name" name = "person_name" /></ p >
#                < p >< label for = "id_comment" > Comment: </ label >< br />< textarea name = "comment" id = "id_comment" rows = "10" cols = "60" ></ textarea ></ p >
#                < p >
#                < input type = "hidden" name = "options" value = "ip" />
#                < input type = "hidden" name = "target" value = "{{ contenttype_id }}:{{ object.id }}" />
#                < input type = "hidden" name = "gonzo" value = { % comment_security_hash object "ip" % } />
#                {{ recaptcha_html }}
#                < input type = "submit" name = "post" value = "Post Comment" />
#                </ p >
#            </ form >

# Now this is hardly an ideal setup, but allows me to use recaptcha with the 
# current trunk comments module. This gives me some time to work on 
# (or find out who is working on) captcha support in the actual trunk.
